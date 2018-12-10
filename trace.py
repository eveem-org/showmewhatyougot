from solver.arithmetic import is_zero
from helpers import opcode

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
