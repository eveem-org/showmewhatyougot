# Show me what you got!
An example implementation of the Eveem.org API.

The project fetches decompiled source codes from:
http://eveem.org/code/0x06012c8cf97bead5deae237070f9587f8e7a266d.json

and analyses them to obtain information about contracts linked to a given one.

Check out showme.py and trace.py for the API documentation.

Created in cooperation with Bloxy.info.

## Installation:
   `git clone https://github.com/kolinko/showmewhatyougot.git`

Execution:
    `python showme.py {address}`
    or
    `python3 showme.py {address}`

### Built-in contracts
Cryptokitties - multiple roles and referenced contracts
    `python showme.py kitties`

DAI medianizer
    `python showme.py medianizer`

Who can call or receive self-destructs
    `python showme.py destruct`

A contract with no source code anywhere
    `python showme.py 0x1f772db718238d8413bad9b309950a9c5286fd71`
