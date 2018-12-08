#
# a part of Panoramix homebrew SMT-solver
#
# originally taken from py-evm/eth/vm/logic/arithmetic.py
# with comments removed to fit the rest of the coding style
# and a lot of duct tape around to handle symbolic stuff
#
# be sure to watch
# https://www.youtube.com/watch?v=8i2idMe142s
# before attempting to modify any of the code

from . import constants


from copy import copy
from . import algebra


'''
    inline imports
'''
def get_opcode(exp):
    if type(exp) in (list, tuple):
        return exp[0]
    else:
        return None


def unsigned_to_signed(value):
    if value <= UINT_255_MAX:
        return value
    else:
        return value - UINT_256_CEILING


def signed_to_unsigned(value):
    if value < 0:
        return value + UINT_256_CEILING
    else:
        return value
'''
    end inline
'''

def simplify_bool(exp):
    if get_opcode(exp) == 'ISZERO':
        inside = simplify_bool(exp[1])

        if get_opcode(inside) == 'ISZERO':
            return inside[1]
        else:
            return is_zero(inside)

    if get_opcode(exp) == 'BOOL':
        return exp[1]

    return exp


def and_op(*args):

    assert len(args) > 1
    left = args[0]

    if len(args) > 2:
        right = and_op(*args[1:])
    else:
        right = args[1]

    if type(left) == int and type(right) == int:
        return left & right

    res = tuple()

    if get_opcode(left) == 'AND':
        res += left[1:]
    else:
        res += (left, )

    if get_opcode(right) == 'AND':
        res += right[1:]
    else:
        res += (right, )

    return ('AND', ) + res

def comp_bool(left, right):
    if left == right:
        return True
    if left == ('BOOL', right):
        return True
    if ('BOOL', left) == right:
        return True
        
    return None

def is_zero(exp):

    if type(exp) == int:
        return exp == 0

    if type(exp) != tuple:
        return ('ISZERO', exp)

    if get_opcode(exp) == 'ISZERO':
        if get_opcode(exp[1]) == 'EQ':
            return exp[1]
        elif get_opcode(exp[1]) == 'ISZERO':
            return is_zero(exp[1][1])
        else:
            return ('BOOL', exp[1])

    if get_opcode(exp) == 'BOOL':
        return is_zero(exp[1])

    if get_opcode(exp) == 'OR':
        res = []
        for r in exp[1:]:
            res.append(is_zero(r))
        return and_op(*res)

    if get_opcode(exp) == 'AND':
        res = []
        for r in exp[1:]:
            res.append(is_zero(r))
        return algebra.or_op(*res)

    if get_opcode(exp) == 'LE':
        return ('GT', exp[1], exp[2])

    if get_opcode(exp) == 'LT':
        return ('GE', exp[1], exp[2])

    if get_opcode(exp) == 'GE':
        return ('LT', exp[1], exp[2])

    if get_opcode(exp) == 'GT':
        return ('LE', exp[1], exp[2])

    if get_opcode(exp) == 'SLE':
        return ('SGT', exp[1], exp[2])

    if get_opcode(exp) == 'SLT':
        return ('SGE', exp[1], exp[2])

    if get_opcode(exp) == 'SGE':
        return ('SLT', exp[1], exp[2])

    if get_opcode(exp) == 'SGT':
        return ('SLE', exp[1], exp[2])


    return ('ISZERO', exp)


def eval_bool(exp, known_true = True):

    if exp == known_true:
        return True

    if is_zero(exp) == known_true:
        return False

    if exp == is_zero(known_true):
        return False

    if type(exp) == int:
        return exp > 0

    if exp in (True, False):
        return True

    if get_opcode(exp) == 'BOOL':
        return eval_bool(exp[1])


    if get_opcode(exp) == 'ISZERO':
        e = eval_bool(exp[1])
        if e != None:
            if e:
                return False
            else:
                return True

    if get_opcode(exp) == 'OR':
        res = 0
        for e in exp[1:]:
            ev = eval_bool(e)
            if type(ev) != None:
                res = res or ev
            else:
                return None

        return res

    if get_opcode(exp) == 'LE':
        left = eval(exp[1])
        right = eval(exp[2])

        if left == right:
            return True

        if type(left) == int and type(right) == int:
            return left <= right
        try:
            return algebra.le_op(left, right)
        except:
            return None


    if get_opcode(exp) == 'LT':
        left = eval(exp[1])
        right = eval(exp[2])

        if left == right:
            return False

        if type(left) == int and type(right) == int:
            return left < right

        try:
            return algebra.lt_op(left, right)
        except:
            return None

    if get_opcode(exp) == 'GT':
        left = eval(exp[1])
        right = eval(exp[2])

        if type(left) == int and type(right) == int:
            return left > right

        if left == right:
            return False
        else:
#            return None
            try:
                le = algebra.le_op(left, right)

                if le == True:
                    return False
                if le == False:
                    return True
                if le is None:
                    return None
            except:
                pass

    if get_opcode(exp) == 'GE':
        left = eval(exp[1])
        right = eval(exp[2])

        if type(left) == int and type(right) == int:
            return left >= right

        if left == right:
            return True
        else:
            try:
                lt = algebra.lt_op(left, right)
                if lt == True:
                    return False
                if lt == False:
                    return True
                if lt is None:
                    return None
            except:
                pass


    if get_opcode(exp) == 'EQ':
        left = eval(exp[1])
        right = eval(exp[2])

        if left == right:
            return True

        if algebra.sub_op(left, right) == 0:
            return True
    aeval = eval(exp)

    return None



def add(left, right):
    return (left + right) & constants.UINT_256_MAX

def addmod(left, right, mode):
    if mod == 0:
        return 0
    else:
        return (left + right) % mod

def sub(left, right):
    if left == right:
        return 0
    else:
        return (left - right) & constants.UINT_256_MAX

def mod(value, mod):
    if mod == 0:
        return 0
    else:
        return value % mod

def smod(value, mod):
    value, mod = map(
        unsigned_to_signed,
        (value, mod),
    )

    pos_or_neg = -1 if value < 0 else 1

    if mod == 0:
        return 0
    else:
        return (abs(value) % abs(mod) * pos_or_neg) & constants.UINT_256_MAX

def mul(left, right):
    if left == 0 or right == 0:
        return 0

    return (left * right) & constants.UINT_256_MAX

def mulmod(left, right, mod):
    if mod == 0:
        return 0
    else:
        return (left * right) % mod

def div(numerator, denominator):
    if numerator == 0:
        return 0

    elif denominator == 0:
        return 0
    else:
        return (numerator // denominator) & constants.UINT_256_MAX

def not_op(exp):
    return constants.UINT_256_MAX - exp

def sdiv(numerator, denominator):
    numerator, denominator = map(
        unsigned_to_signed,
        (numerator, denominator),
    )

    pos_or_neg = -1 if numerator * denominator < 0 else 1

    if denominator == 0:
        return 0
    else:
        return (pos_or_neg * (abs(numerator) // abs(denominator)))

    return signed_to_unsigned(result)

def exp(base, exponent):

    if exponent == 0:
        return 1
    elif base == 0:
        return 0
    else:
        return pow(base, exponent, constants.UINT_256_CEILING)

def signextend(bits, value):

    if bits <= 31:
        testbit = bits * 8 + 7
        sign_bit = (1 << testbit)
        if value & sign_bit:
            return value | (constants.UINT_256_CEILING - sign_bit)
        else:
            return value & (sign_bit - 1)
    else:
        return value

def shl(shift_length, value):

    if shift_length >= 256:
        return 0
    else:
        return (value << shift_length) & constants.UINT_256_MAX


def shr(shift_length, value):

    if shift_length >= 256:
        return 0
    else:
        return (value >> shift_length) & constants.UINT_256_MAX


def sar(shift_length, value):

    value = unsigned_to_signed(value)

    if shift_length >= 256:
        return 0 if value >= 0 else constants.UINT_255_NEGATIVE_ONE
    else:
        return (value >> shift_length) & constants.UINT_256_MAX

opcodes = {
    'ADD': add,
    'ADDMOD': addmod,
    'SUB': sub,
    'MOD': mod,
    'SMOD': smod,
    'MUL': mul,
    'MULMOD': mulmod,
    'DIV': div,
    'SDIV': sdiv,
    'EXP': exp,
    'SIGNEXTEND': signextend,
    'SHL': shl,
    'SHR': shr,
    'SAR': sar,
}


def or_op(left, right):

    return  left | right

def xor(left, right):

    return left ^ right

def byte_op(position, value):

    if position >= 32:
        return 0
    else:
        return (value // pow(256, 31 - position)) % 256

def lt(left, right):

    if left < right:
        result = 1
    else:
        result = 0

    return result

def gt(left, right):

    if left > right:
        result = 1
    else:
        result = 0

    return result

def le(left, right):

    return lt(left, right) | eq(left, right)

def ge(left, right):
    return gt(left, right) | eq(left, right)

def sle(left, right):

    return slt(left, right) | eq(left, right)

def sge(left, right):

    return sge(left, right) | eq(left, right)

def slt(left, right):

    left = unsigned_to_signed(left)
    right = unsigned_to_signed(right)

    if left < right:
        result = 1
    else:
        result = 0

    return result


def sgt(left, right):

    left = unsigned_to_signed(left)
    right = unsigned_to_signed(right)

    if left > right:
        result = 1
    else:
        result = 0

    return result


def eq(left, right):

    if left == right:
        result = 1
    else:
        result = 0

    return result


def eval(exp):
    exp = copy(exp)

    if type(exp) != tuple:
        return exp

    for i,p in enumerate(exp[1:]):
        if get_opcode(p) in opcodes:
            exp = exp[:i+1] + (eval(p),) + exp[i+2:]
#            exp[i+1] = eval(p)

    for p in exp[1:]:
        if type(p) != int:
            return exp

    if exp[0] in opcodes:
        return opcodes[exp[0]](*exp[1:])

    return exp


opcodes.update({
        'AND': and_op,
        'OR': or_op,
        'XOR': xor,
        'NOT': not_op,
        'BYTE': byte_op,
        'EQ': eq,
        'LT': lt,
        'GT': gt,
        'SGT': sgt,
        'SLT': slt,
        'GE': ge,
        'GT': gt,
        'SGE': sge,
        'SLE': sle,
    })


assert eval_bool(eval_bool(('OR', 0, eval_bool(('LT', 480, 18446744073709551615))))) == True

assert hex(eval(('NOT',2))) == '0xfffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffd'
assert eval(('ADD',10,('NOT',1))) == 8

assert eval(('ADD',2,('MUL',2,10))) == 22
assert eval(('ADD',2,10)) == 12
assert eval(('EXP',2,8)) == 256
assert eval(('ADD',2,('MUL',2,'X'))) == ('ADD',2,('MUL',2,'X'))


assert eval(('OR', 256, 256)) == 256

assert True == eval_bool(('ISZERO', ('LT', ('ADD', 384, ('MUL', 1, ('MASK_SHL', 256, 0, 0, ('ADD', 128, ('MUL', 1, 
                    ('MASK_SHL', 251, 0, 5, ('cd', ('ADD', 4, ('MUL', 1, ('cd', 4)))))))))), 
                    ('MASK_SHL', 256, 0, 0, ('ADD', 128, ('MUL', 1, ('MASK_SHL', 251, 0, 5, ('cd', ('ADD', 4, ('MUL', 1, ('cd', 4))))))))))) 
