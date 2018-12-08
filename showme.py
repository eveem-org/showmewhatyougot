import sys

from helpers import opcode, C, prettify
from contract import load_contract

from functools import partial
from collections import defaultdict

from trace import walk_trace

if len(sys.argv) > 1:
    param = sys.argv[1]

    addr_list = {
        'kitties': '0x06012c8cf97BEaD5deAe237070F9587f8E7A266d',
        'default': '0x2Ad180cBAFFbc97237F572148Fc1B283b68D8861',
        'digix': '0xe0b7927c4af23765cb51314a0e0521a9645f0e2a',

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
pretty = partial(prettify, stor_defs)

roles = {}

for s, name in stor_defs.items():
    if s[:3] == ('STORAGE', 160, 0) and len(s) == 4:
        roles[s] = {
            'name': name,
            'definition': s,
            'setters': list(),
            'funcs': set(),
        }

def find_opcodes(line, _):
    return opcode(line)

def get_caller_cond(condition):

    if opcode(condition) != 'EQ':
        if opcode(condition) != 'ISZERO':
            return None
        else:
            condition = condition[1]

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

    return get_caller_cond(condition)



''' finding a list of admins '''

open_access = set(f['hash'] for f in functions.values())

for f in functions.values():
    trace = f['trace']
    assert type(trace) == tuple

    res = walk_trace(trace, find_caller_req)
    if len(res) > 0:
        f['admins'] = set()
        for r in res:
            f['admins'].add(r)
            roles[r]['funcs'].add(f['hash'])
            if f['hash'] in open_access:
                open_access.remove(f['hash'])

    opcodes = walk_trace(trace, find_opcodes)
    side_effects = ['CALL', 'DELEGATECALL', 'CODECALL', 'SELFDESTRUCT', 'STORE']
    # WARN: ^ the above may not be a complete list

    if all(s not in opcodes for s in side_effects):
        # read_only function
        if f['hash'] in open_access:
            open_access.remove(f['hash'])


''' find who can change a given storage '''



def find_stor_req(line, knows_true):
    if opcode(line) != 'STORE':
        return None

    size, offset, stor_num, arr_idx, value = line[1:]

    if len(arr_idx) > 0:
        # we're dealing only with storages that are not arrays
        return None

    callers = []
    for cond in knows_true:
        caller = get_caller_cond(cond)
        if caller is not None:
            callers.append(caller)

    return ('STORAGE', size, offset, stor_num), callers

for f in functions.values():
    trace = f['trace']

    res = walk_trace(trace, find_stor_req)
    if len(res) > 0:
#        print()
#        print(f['color_name'])
        for (stor, callers) in res:
#            print('changes', pretty(('STORAGE',)+stor))
#            print(', '.join(pretty(c) for c in callers))
            if stor in roles:
                if callers is not None:
                    setter = (callers, f['name'])
                else:
                    setter = ('anyone', f['name'])

                if setter not in roles[stor]['setters']:
                    roles[stor]['setters'].append(setter)

print(f'\n{C.blue} # contract roles{C.end}')
for stor in roles:
    print(C.blue, pretty(stor), C.end)

    if len(roles[stor]['setters']) > 0:
        print('  can be changed by:')
        for callers, f_name in roles[stor]['setters']:
            print('  ', C.green, (', '.join(pretty(c) for c in callers)), C.end, 'in', f_name)
    else:
        print('  constant')

    role = roles[stor]
    if len(role['funcs']) > 0:
        print()
        print('  can call those functions:')

        for f_hash in role['funcs']:
            func = functions[f_hash]

            print('   ', func['color_name'])
        print()

    print()
'''
print(C.green, 'anyone', C.end)
for f_hash in open_access:
    func = functions[f_hash]
#    if func['']
    print('- ', func['color_name'])

print()
'''


'''


def find_returns(line, _):
    if opcode(line) == 'RETURN':
        return line
    else:
        return None

    res = walk_trace(trace, find_returns)
    if len(res) > 0:
        print()
        print(f['color_name'])
        for ret in res:
            print('returns', ret)

    continue


'''








