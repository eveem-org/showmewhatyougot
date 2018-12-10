from helpers import opcode, is_zero

'''
    Two helper functions to analyse the function traces outputted by
    http://eveem.org/code/0x06012c8cf97bead5deae237070f9587f8e7a266d.json

    The intermediate language used is not documented anywhere yet in full,
    but you should get a good understanding of it by analysing the kitties code linked above.
'''

'''
    Some opcodes that may not be obvious:
'''

'''
    (MASK_SHL, size, offset, shl, expression)
    is the same as:
    (SHL, (MASK, size, offset, expression), shl)
    
    Where "shl" may be negative, in which case it means SHR.

    For example:
    (MASK_SHL, 4, 16, -8, 0xF00)
    == 0x70

    (MASK_SHL, 160, 0, 0, 'CALLER')
    == address(caller) - that is, first 160 bytes of the call sender

    (MASK_SHL, 160, 0, 0, 'call.data')
    == adress(call.data[len(call.data)-1])

    (MASK_SHL, 256, call.data.length-256, 0, 'call.data')
    == call.data[0]

    MASK_SHL is a super-unobvious construct, and it's hard to wrap your head around,
    but simplifies very many things.
'''

'''
    Accessing storage:

    (STORAGE, size, offset, num[, idx])
    == MASK_SHL(size, offset, (Storage num[idx]))

    E.g.
    (STORAGE, 160, 0, 1)
    == address at Storage#1

    (STORAGE, 256, 0, 2, (MASK_SHL, 160, 0, 0, _from))
    == Storage#2[addr(_from)] # so, Storage#2 is a mapping addr=>uint256
'''

'''
    (WHILE, condition, trace)
    repeats trace execution until the condition is no longer true
'''

'''
    (LOOP, trace, label)
    where
    trace == (line, line..., line, (END_LOOP, label) )

    executes trace
'''

'''
    (IF, condition, trace_if_true, trace_if_false)
    An "if" statement

    Important:
    'if' statements is that they are always at the end of a trace
    (i.e. there are no lines after the 'if' statement)

    So, if a contract is following:

    do_stuff
    if condition:
        do_A
    else:
        do_B
    do_some_more_stuff

    The trace will be like this:

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

    And never like this:
    [
    do_stuff,
    [IF, condition, [do_A], [do_B]],
    do_some_more_stuff
    ]

    This makes the traces potentially extremely long, and difficult to read,
    but has the benefit of extremely easy analysis 

    As an example, see:
        http://eveem.org/code/0x06012c8cf97bead5deae237070f9587f8e7a266d.json
    Function
        setSecondsPerBlock(uint256 _secs)

    The human-readable, decompiled form (in 'print' attr in json, or on eveem.org) is short,
    the trace is much longer
'''

'''
    As for the other opcodes, they are not yet documented, but should be relatively understandable.
    Put up a github issue if you have problems understanding:
    https://github.com/kolinko/showmewhatyougot/issues

    Also, the best way is to just print out the trace, and compare it to the decompiled output
    on http://www.eveem.org/, or to the one in "print".
'''

def walk_trace(trace, f=print, knows_true=None):
    '''
        
        walks the trace, calling function f(line, knows_true) for every line
        knows_true is a list of 'if' conditions that had to be met to reach a given
        line

    '''
    res = []
    knows_true = knows_true or []

    for idx, line in enumerate(trace):
        found = f(line, knows_true)

        if found is not None:
            res.append(found)

        if opcode(line) == 'IF':
            condition, if_true, if_false = line[1:]
            res.extend(walk_trace(if_true, f, knows_true + [condition]))
            res.extend(walk_trace(if_false, f, knows_true + [is_zero(condition)]))

            assert idx == len(trace)-1 # IFs always end the trace tree
            continue

        if opcode(line) == 'WHILE':
            condition, trace = line[1:]
            res.extend(walk_trace(trace, f, knows_true + [is_zero(condition)]))
            continue

        if opcode(line) == 'LOOP':
            trace, label = line[1:]
            res.extend(walk_trace(trace, f, knows_true))

    return res


def walk_exp(exp, f=print):
    '''
        walks the expression - a more generic version of walk_trace.
        useful for finding expressions of a given type (like 'all storages in the trace')
    '''

    found = f(exp)
    res = [found] if found is not None else []

    if type(exp) == tuple:
        for e in exp:
            res.extend(walk_exp(e, f))

    return res
