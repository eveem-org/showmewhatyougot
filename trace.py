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

    for line in trace:
        found = f(line, knows_true)

        if found is not None:
            res.append(found)

        if opcode(line) == 'IF':
            condition, if_true, if_false = line[1:]
            res.extend(walk_trace(if_true, f, knows_true + [condition]))
            res.extend(walk_trace(if_false, f, knows_true + [is_zero(condition)]))
            continue

        if opcode(line) == 'WHILE':
            condition, trace = line[1:]
            res.extend(walk_trace(trace, f, knows_true + [is_zero(condition)]))
            continue

        if opcode(line) == 'LOOP':
            trace, label = line[1:]
            res.extend(walk_trace(trace, f, knows_true))

    return res