import urllib
import urllib.request
import json

import os

address = "0x2Ad180cBAFFbc97237F572148Fc1B283b68D8861"
url = f"http://eveem.org/code/{address}.json"
cache_fname = f'cache/{address}.json'

print(url)


if os.path.isfile(cache_fname):
    with open(cache_fname) as f:
        contract = json.loads(f.read())
else:

    with urllib.request.urlopen(url) as response:
        re = response.read()
        contract = json.loads(re)

        with open(fname, 'w') as f:
            f.write(json.dumps(contract, indent=2))

functions = contract['functions']

for f in functions:
    print(f['color_name'])