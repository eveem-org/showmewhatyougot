import sys

from helpers import opcode, C, prettify
from contract import load_contract

from functools import partial


if len(sys.argv) > 1:
    address = sys.argv[1]

    addr_list = {
        'kitties': '0x06012c8cf97BEaD5deAe237070F9587f8E7A266d',
        'default': '0x2Ad180cBAFFbc97237F572148Fc1B283b68D8861',
    }

    if address in addr_list:
        address = addr_list[address]
else:
    print("\n\n\tusage `python showme.py {address}`\n\n")
    exit()


functions, stor_defs = load_contract(address)
pretty = partial(prettify, stor_defs)

print(pretty('test'))


def walk_trace(trace, f=print):

    res = []

    for line in trace:
        found = f(line)
        if found is not None:
            res.append(found)

        if opcode(line) == 'IF':
            condition, if_true, if_false = line[1:]
            res.extend(walk_trace(if_true, f))
            res.extend(walk_trace(if_false, f))
            continue

        if opcode(line) == 'WHILE':
            condition, trace = line[1:]
            res.extend(walk_trace(trace, f))
            continue

    return res


def find_caller_req(line):
    # finds IFs: (IF (EQ caller, storage))

    if opcode(line) != 'IF':
        return None

    condition, if_true, if_false = line[1:]

    if opcode(condition) != 'EQ':
        if opcode(condition) != 'ISZERO':
            return None
        else:
            condition = condition[1]
            if_true, if_false = if_false, if_true

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



print(f'\n{C.blue} # admins{C.end}')

for f in functions.values():
    trace = f['trace']
    assert type(trace) == tuple

    res = walk_trace(trace, find_caller_req)
    if len(res) > 0:
        print(f['color_name'])
        f['admins'] = set()
        for r in res:
            f['admins'].add(r)
#            print(r)

        print(f['admins'])



print()
