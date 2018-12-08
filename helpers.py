'''
    various small helper functions
    
'''


def opcode(exp):
    if type(exp) in (list, tuple):
        return exp[0]
    else:
        return None


def deep_tuple(exp):
    if type(exp) != list:
        return exp

    return tuple(deep_tuple(e) for e in exp)
