'''
    ShowMe parses output from Panoramix / eveem.org, and delivers some fun facts
    about the contract
'''

'''

    The eveem API is open here:
    http://eveem.org/code/{address}.json
    e.g.
    http://eveem.org/code/0x06012c8cf97bead5deae237070f9587f8e7a266d.json

    The most important field in the API is the 'trace'.

    Trace has the function code in an intermediate language, and in the form that
    was designed to be easily parsable by analytics tools.


    To understand the 'trace' structure better, see comments in trace.py.

'''

import sys

from helpers import opcode, C, is_zero
from contract import load_contract
from storage import read_address

from functools import partial
from collections import defaultdict

from trace import walk_trace, walk_exp
from roles import Roles

if len(sys.argv) > 1:
    param = sys.argv[1]

    addr_list = {
        'kitties': '0x06012c8cf97BEaD5deAe237070F9587f8E7A266d',
        'default': '0x2Ad180cBAFFbc97237F572148Fc1B283b68D8861',
        'digix': '0xe0b7927c4af23765cb51314a0e0521a9645f0e2a',
        'aragon': '0x960b236a07cf122663c4303350609a66a7b288c0',
        'medianizer': '0x729d19f657bd0614b4985cf1d82531c67569197b',
        'dai': '0x729d19f657bd0614b4985cf1d82531c67569197b',
        'arbitrager': '0xc2a694c5ced27e3d3a5a8bd515a42f2b89665003',
        'nocode': '0x1f772db718238d8413bad9b309950a9c5286fd71',
        'destruct': '0xB02bD126cd5477b2C166f8A31fAb75DB0c074371',
    }

    if param in addr_list:
        contract_name = param
        address = addr_list[param]
    else:
        address = param
        contract_name = None

else:
    print("\n\n\tusage `python showme.py {address}`\n\n")
    exit()

functions, stor_defs = load_contract(address, contract_name)
roles = Roles(functions, stor_defs)

def find_opcodes(line, _):
    return opcode(line)

def get_caller_cond(condition):
    #  checks if the condition has this format:
    #  (EQ (MASK_SHL, 160, 0, 0, 'CALLER'), (STORAGE, size, offset, stor_num))

    #  if it does, returns the storage data
    #
    #  also, if condition is IS_ZERO(EQ ...), it turns it into just (EQ ...)
    #  -- technically not correct, but this is a hackathon project, should be good enough :)

    if opcode(condition) != 'EQ':
        return None

    if condition[1] == ('MASK_SHL', 160, 0, 0, 'CALLER'):
        stor = condition[2]
    elif condition[2] == ('MASK_SHL', 160, 0, 0, 'CALLER'):
        stor = condition[1]
    else:
        return None

    if opcode(stor) == 'STORAGE' and len(stor) == 4:
        # len(stor) == 5 -> indexed storage array, not handling those now
        return stor
    else:
        return None


def find_caller_req(line, _):
    # finds IFs: (IF (EQ caller, storage))

    if opcode(line) != 'IF':
        return None

    condition, if_true, if_false = line[1:]

    return get_caller_cond(condition) or get_caller_cond(is_zero(condition))


''' 
    
    finding a list of admins -
    if the function checks for caller in any way,
    it returns that comparison as a potential admin

'''

state_changing_functions = set()

for f in functions.values():
    trace = f['trace']
    opcodes = walk_trace(trace, find_opcodes)

    side_effects = ['CALL', 'DELEGATECALL', 'CODECALL', 'SELFDESTRUCT', 'STORE', 'CREATE', 'CREATE2']
    # WARNING: not sure if this is the whole list of state changing operations
    #           but this is just an API demo...


    # if there are opcodes that cause side effects, we add this
    # function to a list of state_changing functions

    if any(s in opcodes for s in side_effects):
        state_changing_functions.add(f['hash'])

# let's start by assuming anyone can call every function
roles['anyone'].funcs = state_changing_functions


for f in functions.values():
    trace = f['trace']
    assert type(trace) == tuple

    res = walk_trace(trace, find_caller_req)
    if len(res) > 0:
        for r in res:
            roles[r].funcs.add(f['hash'])
            if f['hash'] in roles['anyone'].funcs:
                roles['anyone'].funcs.remove(f['hash'])


''' 
    
    find who can change a given storage 

'''

def find_stor_req(line, knows_true):
    # for every line, check if it's (STORE, size, offset, stor_num, _, some value)
    # if it is, it means that the line writes to storage...

    if opcode(line) != 'STORE':
        return None

    _, size, offset, stor_num, arr_idx, value = line

    if len(arr_idx) > 0:
        # we're dealing only with storages that are not arrays for now
        return None

    # ok, so it's a storage write - let's backtrack through all the IFs we encountered
    # before, and see if there were checks for callers there

    callers = []
    for cond in knows_true:
        caller = get_caller_cond(cond)
        if caller is not None:
            callers.append(caller)

    if len(callers) == 0:
        callers = ['anyone']

    return ('STORAGE', size, offset, stor_num), callers


for f in functions.values():

    for (stor, callers) in walk_trace(f['trace'], find_stor_req):

        affected_roles = set()
        for r in roles:

            if opcode(r) != 'STORAGE':
                continue

            assert opcode(stor) == 'STORAGE'

            _, stor_size, stor_offset, stor_num = stor[:4]
            _, role_size, role_offset, role_num = r[:4]

            if stor_num == role_num and \
               role_offset <= stor_offset < role_offset + role_size:

                affected_roles.add(r)

                # ^ for a role (STORAGE, 160, 0, 1), will catch those:
                #
                #   (STORE, 160, 0, 1, value) (exact match)
                #   (STORE, 256, 0, 1, value) (overwrites a bigger part of the storage containing this role)
                #   (STORE, 8, 16, 1, value) (overwrites a part of the role's storage - should never happen really)
                #
                # and ignores such writes
                #   (STORE, 8, 160, 1, value)

                # check pause() of `kitties` to see why some writes are ignored
                # check setOwner() of `digix` to see why sometimes a bigger part of storage is written

        setter = (callers, f['name'])

        for role_id in affected_roles:
            if setter not in roles[role_id].setters:
                roles[role_id].setters.append(setter)


'''

    browse all the contract calls, and figure out who gets withdrawals, and what contracts
    can get called

'''


def find_calls(line, _):
    # todo: delegatecalls
    # todo: selfdestructs
    if opcode(line) != 'CALL':
        return None

    _, addr, wei, _, _, _, _, f_name, f_params = line[1:]

    if addr == ('MASK_SHL', 160, 0, 0, 'CALLER'):
        # WARN: should check for knows_true, perhaps a caller can only be someone specific
        addr = 'anyone'
    elif opcode(addr) != 'STORAGE' or len(addr) > 4:
        addr = 'unknown'

    return (addr, wei, f_name, f_params)


for f in functions.values():
    trace = f['trace']

    res = walk_trace(trace, find_calls)

    for addr, wei, f_name, f_params in res:
        if wei != 0:
            # withdrawal
            roles[addr].withdrawals.add(f['hash'])
        else:
            roles[addr].calls.add(f['hash'])


'''

    find self-destructs

'''

def find_destructs(line, knows_true):
    # todo: delegatecalls
    # todo: selfdestructs
    if opcode(line) != 'SELFDESTRUCT':
        return None

    receiver = line[1]

    if receiver == ('MASK_SHL', 160, 0, 0, 'CALLER'):
        receiver = 'anyone'
    elif opcode(receiver) != 'STORAGE' or len(receiver) > 4:
        receiver = 'unknown'

    callers = []
    for cond in knows_true:
        caller = get_caller_cond(cond)
        if caller is not None:
            callers.append(caller)

    if len(callers) == 0:
        callers = ['anyone']

    return receiver, callers


for f in functions.values():
    trace = f['trace']

    res = walk_trace(trace, find_destructs)

    for receiver, callers in res:
        if receiver not in roles:
            add_role(definition=addr)

        roles[receiver]['destructs'].add(f['hash'])

        for caller in callers:
            roles[caller]['destructs_init'].add(f['hash'])



'''

    display

'''
print(f'\n{C.blue} # contract roles{C.end}')
print()

for stor in roles:
    role = roles[stor]

    if len(role.funcs) == 0 and len(role.withdrawals) == 0 and len(role.calls) == 0:
        continue

    print(C.blue, role.name, C.end)

    if roles[stor].setters:
        print('  can be changed by:')
        for callers, f_name in roles[stor].setters:
            print('  ', C.green, (', '.join(roles[c].name for c in callers)), C.end, 'in', f_name)
        print()

    else:
        if opcode(stor) == 'STORAGE':
            print('  constant')
            print()

    if len(role.funcs) > 0:
        print('  can call those functions:')

        for f_hash in role.funcs:
            func = functions[f_hash]

            print('   ', func['color_name'])
        print()

    if len(role.withdrawals) > 0:
        print('  can receive withdrawal through:')

        for f_hash in role.withdrawals:
            func = functions[f_hash]

            print('   ', func['color_name'])

        print()

    if len(role.calls) > 0:
        print('  can be called by:')

        for f_hash in role.calls:
            func = functions[f_hash]

            print('   ', func['color_name'])

        print()

    if len(role.destructs) > 0:
        print('  can receive selfdestruct:')

        for f_hash in role.destructs:
            func = functions[f_hash]

            print('   ', func['color_name'])

        print()

    if len(role.destructs_init) > 0:
        print('  can initiate selfdestruct:')

        for f_hash in role.destructs_init:
            func = functions[f_hash]

            print('   ', func['color_name'])

        print()

#    print('  current value:\n','  ',str(roles[stor]['value']))



    print()


