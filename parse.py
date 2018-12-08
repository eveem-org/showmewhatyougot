import urllib
import urllib.request
import json

url = "http://eveem.org/code/0x2Ad180cBAFFbc97237F572148Fc1B283b68D8861.json"

with urllib.request.urlopen(url) as response:
    re = response.read()
    res = json.loads(re)

    print(res)