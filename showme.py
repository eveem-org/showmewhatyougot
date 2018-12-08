import sys

from helpers import opcode, C
from contract import load_contract

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

print()
print(f'{C.blue} contract{C.end} {address}')

functions, stor_defs = load_contract(address)


def walk_trace(trace):
    for line in trace:
        if opcode(line) == 'IF':
            condition, if_true, if_false = line[1:]
            walk_trace(if_true)
            walk_trace(if_false)
            continue

        if opcode(line) == 'WHILE':
            condition, trace = line[1:]
            walk_trace(trace)
            continue

        




for f in functions.values():
    trace = f['trace']
    assert type(trace) == tuple

    walk_trace(trace)

print()
