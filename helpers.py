'''
    various small helper functions

'''


def opcode(exp):
    if type(exp) in (list, tuple):
        return exp[0]
    else:
        return None


def prettify(stor_defs, exp):
    if opcode(exp) == 'STORAGE' and exp in stor_defs:
        return stor_defs[exp]
    else:
        return exp


def deep_tuple(exp):
    if type(exp) != list:
        return exp

    # converts (mask_shl, size, 0, 0, (storage, size, offset, val)) ->
    #               -> (storage, size, offset, val)  

    if len(exp) == 0:
        return tuple()

    if exp[0] == 'MASK_SHL' and (exp[2], exp[3]) == (0, 0) and opcode(exp[4]) == 'STORAGE' and\
        exp[1] == exp[4][1]:
            return deep_tuple(exp[4])

    return tuple(deep_tuple(e) for e in exp)


'''
    Copied from Panoramix
'''
class C:
    end = '\033[0m'

    header = '\033[95m'
    blue = '\033[94m'
    okgreen = '\033[92m'
    warning = '\033[93m'
    fail = '\033[91m'
    bold = '\033[1m'
    underline = '\033[4m'
    green = '\033[32m'
    gray = '\033[38;5;8m'
