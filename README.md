# # Show me what you got
An example implementation of the Eveem.org API.

The project fetches decompiled source codes from:
http://eveem.org/code/0x06012c8cf97bead5deae237070f9587f8e7a266d.json

and analyses them to obtain information about contracts linked to a given one.

Check out showme.py and trace.py for the API documentation.

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

## Eveem.org API
Eveem.org runs or Panoramix - a symbolic execution EVM decompiler.
Panoramix will be open-sourced as soon as the code gets to the state of semi-understandability.

The API is fully open though, and it’s a nice starting point to understand how the decompiler works, and build stuff on top of it.

The eveem API is open here:

`http://eveem.org/code/{address}.json`

e.g.

`http://eveem.org/code/0x06012c8cf97bead5deae237070f9587f8e7a266d.json`

The most important field in the API is the 'trace'.
Trace has the function code in an intermediate language, and in the form that was designed to be easily parsable by analytics tools.

### Understanding “trace”
A good starting point to understanding Panoramix traces is the crypto kitties contract, since it contains all the possible weird edge cases:
`http://eveem.org/code/0x06012c8cf97bead5deae237070f9587f8e7a266d.json`

The intermediate language used is not documented anywhere yet in full,
but you should get a good understanding of it by analysing the kitties code linked above.

Below, some of the opcodes that may be hard to get.

Also, check out *trace.py* and *walk_trace* function there.

#### (MASK_SHL, size, offset, shl, expression)
==
`(SHL, (MASK, size, offset, expression), shl)`

Where "shl" may be negative, in which case it means SHR.

For example:
```
(MASK_SHL, 4, 16, -8, 0xF00)
== 0x70
```

```
(MASK_SHL, 160, 0, 0, 'CALLER')
== address(caller) - that is, first 160 bytes of the call sender
```

```
(MASK_SHL, 160, 0, 0, 'call.data')
== adress(call.data[len(call.data)-1])
```

```
(MASK_SHL, 256, call.data.length-256, 0, 'call.data')
== call.data[0]
```

#### (STORAGE, size, offset, num[, idx])
`== MASK_SHL(size, offset, (Storage num[idx]))`
(reads storage of a given location and index)

E.g.
```
(STORAGE, 160, 0, 1)
== address at Storage#1
```

```
(STORAGE, 256, 0, 2, (MASK_SHL, 160, 0, 0, _from))
== Storage#2[addr(_from)] # so, Storage#2 is a mapping addr=>uint256
```

#### (STORE, size, offset, num, idx, value)
Writes to the storage

E.g.

`(STORE, 160, 0, 1, null, (MASK_SHL, 160, 0, 0, 'CALLER'))`

writes function caller address to first 160 bits of Storage 1
(remaining bits of the storage stay untouched)

```
(STORE, 256, 0, 2, _receiver, (ADD, 1, (STORAGE, 256, 0, 2, _receiver)))
=> stor_2[_receiver] = stor_2[_receiver] + 1
```

#### (WHILE, condition, trace)
repeats trace execution until the condition is no longer true

e.g.

```
(WHILE, (LE, (var, 1), 100), 
	[ (STORE, 256, 0, 1, (var, 1), 123),
         (setvar, 1, (add (var, 1), 10)) ]
```

is the same as:

```
while var1<100:
  storage1[var1] = 123
  var1 += 10
```

#### (LOOP, trace, label)
where

`trace == (line, line..., line, (END_LOOP, label) )`

executes trace until END_LOOP, and then repeats.

Panoramix always tries to replace LOOPs with WHILEs, but sometimes it doesn’t yet know how.

you can read:

`(LOOP, [ do_sth, do_sth, (END_LOOP hello) ], hello)`

as:

```
label hello
do_sth
do_sth
goto hello
```

#### (IF, condition, trace_if_true, trace_if_false)

Panoramix produces a very specific kind of ‘if’ statements, described below. The syntax is done in such a way that is as easy to parse automatically as possible.

Important:
*’if' statements is that they are always at the end of a trace
(i.e. there are no lines after the 'if' statement)*

So, if a contract is following:

`do_stuff`
`if condition:`
`	do_A`
`else:`
`	do_B`
`do_some_more_stuff`

The trace will be like this:

```
[
do_stuff,
[IF, condition, [
	do_A,
	do_some_more_stuff
	],[
	do_B,
	do_some_more_stuff
	]
]
]
```

And *never* like this:

```
[
do_stuff,
[IF, condition, [do_A], [do_B]],
do_some_more_stuff
]
```

This makes the traces potentially extremely long, and difficult to read,
but has the benefit of extremely easy analysis 

As an example, see:
`http://eveem.org/code/0x06012c8cf97bead5deae237070f9587f8e7a266d.json`

function
`setSecondsPerBlock(uint256 _secs)`

The human-readable, decompiled form (in 'print' attr in json, or on eveem.org) is short, the trace is much longer

#### Other opcodes
As for the other opcodes, they are not yet documented, but should be relatively understandable.

Put up a github issue if you have problems understanding:
https://github.com/kolinko/showmewhatyougot/issues

Also, the best way is to just print out the trace, and compare it to the decompiled output on http://www.eveem.org/, or to the one in "print".
