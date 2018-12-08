import urllib
import urllib.request
import json

import os

from helpers import opcode, deep_tuple, C

address = "0x2Ad180cBAFFbc97237F572148Fc1B283b68D8861"
print()
print(f'{C.blue} contract{C.end} {address}')


url = f"http://eveem.org/code/{address}.json"
cache_fname = f'cache/{address}.json'

print(url)
print()

if os.path.isfile(cache_fname):
    with open(cache_fname) as f:
        contract = json.loads(f.read())
else:

    with urllib.request.urlopen(url) as response:
        re = response.read()
        contract = json.loads(re)

        with open(fname, 'w') as f:
            f.write(json.dumps(contract, indent=2))

functions = {}

stor_defs = {}

print()
print(C.blue,'functions',C.end)

for f in contract['functions']:
    for k, v in f.items():
        # converting all the traces, and so on into tuples from lists
        # tuples are read-only, which we want, and also can work as indexes easier

        f[k] = deep_tuple(v)

    functions[f['hash']] = f

    print(f['color_name'])

    if f['getter']:
        stor_defs[f['name']] = f['getter']

print()
print(C.blue, 'storage definitions', C.end)


for k,v in stor_defs.items():
    print(k, v)