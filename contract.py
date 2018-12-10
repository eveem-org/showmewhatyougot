import urllib
import urllib.request
import json

import os

from helpers import opcode, deep_tuple, C

def load_contract(address, name=None):
    print()
    if name:
        print(f'{C.blue} # contract{C.end} {C.header}{name} -- {address}{C.end}')
    else:
        print(f'{C.blue} # contract{C.end} {C.header}{address}{C.end}')


    url = f"http://eveem.org/code/{address}.json"
    cache_fname = f'cache/{address}.json'

    if not os.path.isdir('cache'):
        os.mkdir('cache')

    if os.path.isfile(cache_fname):
        with open(cache_fname) as f:
            contract = json.loads(f.read())
    else:
        print(f'{C.blue} # fetching {url}...{C.end}')
        with urllib.request.urlopen(url) as response:
            re = response.read()
            contract = json.loads(re)

            with open(cache_fname, 'w') as f:
                f.write(json.dumps(contract, indent=2))



    functions = {}
    stor_defs = {}

    for f in contract['functions']:
        if f is None:
            continue

        for k, v in f.items():
            # converting all the traces, and so on into tuples from lists
            # tuples are read-only, which we want, and also can work as dict indexes easier

            f[k] = deep_tuple(v)

        functions[f['hash']] = f

        if f['getter']:
            stor_defs[f['getter']] = f['name'].split('(')[0]

    return functions, stor_defs


