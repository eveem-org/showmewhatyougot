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
