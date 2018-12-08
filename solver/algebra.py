# a part of panoramix homebrew smt-solver
#
# written in some crazy duct-tape sprint, don't trust it too much

def logprint(*args):
#    print(*args)
    pass

class PlusInf():
    def __str__(self):
        return "PlusInf()"


class MinusInf():
    def __str__(self):
        return "MinusInf()"

class CannotCompareError(Exception):
    pass


# copied from other modules, and a bit from y-evm need to rework module structures
# to avoid circular dependencies

UINT_256_MAX = 2**256 - 1

def get_opcode(exp):
    if type(exp) in (list, tuple):
        return exp[0]
    else:
        return None

def all_concrete(*args):
    for a in args:
        if type(a) not in (int, float):
            return False
    return True

def mask_to_int(size, offset):
        return (2**size-1)*(2**offset)

def _sub(left, right):
    if left == right:
        return 0
    else:
        return (left - right) & UINT_256_MAX

def get_bit(num, pos):
    return num & (1 << pos)

def to_real_int(exp):
    if type(exp) == int and exp < -15792089237316195423570985008687907853269984665640564039457584007913129639934:
        return -(to_real_int(-exp))
    if type(exp) == int and get_bit(exp, 255):
        return -_sub(0,exp)
    else:
        return exp

# /end copied


def lower_bound(exp):
    if exp == 'CALLDATASIZE':
        return 6 # it should be 4, but sweeper contract works badly then.
    else:
        return 0

def upper_bound(exp):
    if get_opcode(exp) != 'MASK_SHL':
        return None

    if exp[3] != 0:
        return None

    return (2**exp[2]+exp[1])-1

def add_ge_zero(exp): 
    assert get_opcode(exp) == 'ADD', exp
    assert len(exp)>2, exp

    exp = exp[1:]

    if type(exp[0]) == int:
        real = to_real_int(exp[0])
        real_2 = to_real_int(exp[0])
        exp = exp[1:]
    else:
        real = 0
        real_2 = 0

    if real >= 0:

        for e in exp:

            if get_opcode(e) != 'MUL':
                continue

            assert len(e) == 3 # otherwise we need to deal with that

            if e[1] >= 0:  
                continue

            assert e[1] < 0

            if upper_bound(e[2]) is None:
                real = -1
                break
            elif upper_bound(e[2]) is not None:
                real += e[1] * upper_bound(e[2])

        if real >= 0:
            return True

        # let's test for negative...

        real = real_2

        for e in exp:

            if get_opcode(e) != 'MUL':
                continue

            assert len(e) == 3 # otherwise we need to deal with that

            if e[1] >= 0:  
                continue

            assert e[1] < 0

            real += e[1] * lower_bound(e[2])

        if real < 0:
            return False


    elif real <= 0:

        for e in exp:
            if get_opcode(e) != 'MUL':
                return None

            assert len(e) == 3

            if e[1] <= 0:
                continue

            assert e[1] > 0

            if upper_bound(e[2]) is None:
                return None
            else:
                real += e[1] * upper_bound(e[2])


        if real < 0:
            return False


    return None




def minus_op(exp):

    return mul_op(-1, exp)

def sub_op(left, right):

    if (type(left), type(right)) == (int, int):
        return left-right # optimisation

    if left == 0:
        return minus_op(right)

    if right == 0:
        return left

    return add_op(left, minus_op(right))

def flatten_adds(exp):
    res = exp

    while len([a for a in res if get_opcode(a) == 'ADD']) > 0:
        exp = []
        for r in res:
            if get_opcode(r) == 'ADD':
                assert len(r[1:])>1
                exp += r[1:]
            else:
                exp.append(r)

        res = exp

    return res

add_dict = {}
def add_op(*args):
    if args in add_dict:
        return add_dict[args]

    ret = _add_op(*args)
    add_dict[args] = ret
    return ret


def _add_op(*args):
    #print('add', args)
    assert len(args) > 1
    assert 'MUL' not in args # some old bug, it's ok for ['MUL'..] to be in args, but not 'MUL' directly

    # speed optimisation
    real = 0
    all_concrete = True
    for r in args:
        if type(r) in (int, float):
            real += r
        else:
            all_concrete = False

    if all_concrete:
        return real
    # / speed

    res = flatten_adds(list(args))

    for r in res:
        if type(r) in [PlusInf, MinusInf]:
            res2 = list(args)
            res2.remove(r)
            assert minus_op(r) not in res2, res # PlusInf and MinusInf shouldn't be in the same add
            return r

    for idx,r in enumerate(res):
        if get_opcode(r) != 'MUL':
            res[idx] = mul_op(1, r)

    real = 0
    symbolic = []

    for r in res:
        assert get_opcode(r) != 'ADD'

        if type(r) in [int,float]:
            real += r 
        else:
            assert get_opcode(r) == 'MUL'

            found = False

            for idx, rr in enumerate(symbolic):
                tried = try_add(r, rr)

                if tried is None:
                    tried = try_add(rr, r)

                if tried is not None and tried != 0:
                    found = True

                    if get_opcode(tried) == 'MUL':
                        symbolic[idx] = tried
                    else:
                        assert get_opcode(tried) == 'ADD'
                        assert len(tried) == 3
                        assert type(tried[1]) == int
                        assert get_opcode(tried[2]) == 'MUL'

                        symbolic[idx] = tried[2]
                        real += tried[1]

                    break

            if not found:
                symbolic.append(r)

    symbolic = tuple(s for s in symbolic if s[1] != 0)

    res = (real, ) + symbolic

    assert 'MUL' not in symbolic # same as above, some old bug

    if len(res) == 1:
        return res[0]

    if res[0] == 0 and len(symbolic) == 1:
        return symbolic[0]

    if res[0] == 0:
        return ('ADD', ) + symbolic

    assert len(res)>1
    return ('ADD', ) + res

def mul_op(*args):
    # super common
    if len(args) == 2 and type(args[0]) in [int, float] and type(args[1]) in (int, float):
        return args[0] * args[1]

    assert len(args) > 1
    assert 'MUL' not in args

    if len(args) == 2 and type(args[0]) in [int, float] and type(args[1]) in (PlusInf, MinusInf):
        real = args[0]

        if type(args[1]) == PlusInf and real < 0:
            return MinusInf()
        elif type(args[1]) == MinusInf and real < 0:
            return PlusInf()

        return args[1]

    assert PlusInf not in args # not supported yet
    assert MinusInf not in args # not supported yet

    res = tuple()

    for a in args:
        if get_opcode(a) == 'MUL':
            res += a[1:]
        else:
            res += (a, )

    add_list = tuple(a for a in res if get_opcode(a) == 'ADD')  # list(filter(lambda a: get_opcode(a) == 'ADD', res))

    if len(add_list) > 0:
        el = add_list[0]
        assert get_opcode(el) == 'ADD'

        without = list(res)
        without.remove(el)

        ret = tuple(mul_op(x, *without) for x in el[1:])
        return add_op(*ret)

    real = 1
    symbolic = tuple()

    for r in res:
        assert get_opcode(r) != 'ADD'

        if r == 0:
            return 0
        elif type(r) in (int, float):
            real = int(real * r) # arithmetic, or regular?
        else:
            symbolic += (r, )

    assert len(symbolic) == 0 or symbolic[0] != 'MUL' # some old bug

    if len(symbolic) == 0:
        return real
    else:
        return ('MUL', real, ) + symbolic

def get_sign(exp):
    if exp == 0:
        return 0

    elif ge_zero(exp) and ge_zero(sub_op(0, exp)) == False:
        return 1
    elif ge_zero(exp) == False:
        return -1
    else:
        return None

def safe_ge_zero(exp):
    try:
        return ge_zero(exp)
    except CannotCompareError:
        return None

def ge_zero(exp):
    # returns True if exp>=0, False if exp<=0, CannotCompareError if it doesn't know

    if type(exp) in (int, float):
        return exp >= 0

    if type(exp) == str:
        return True

    if get_opcode(exp) == 'MUL':
        counter = 1
        for e in exp[1:]:
            c = ge_zero(e)
            if c == True:
                counter *= 1
            elif c == False:
                counter *= -1
            
        return counter >= 0
            
    if get_opcode(exp) == 'BOOL':
        return True

    if get_opcode(exp) == 'MASK_SHL':
        return ge_zero(exp[4])

    if get_opcode(exp) in ['cd', 'STORAGE', 'MSIZE']:
        return True

    if type(exp) == PlusInf:
        return True

    elif type(exp) == MinusInf:
        return False

    if get_opcode(exp) in ['ADD', 'OR']:

        ret = add_ge_zero(exp)

        if ret is None:
            raise CannotCompareError
        else:
            return ret

    if get_opcode(exp) == 'var': # dangerous, assuming variables are >= 0!
        return True

    raise CannotCompareError

def lt_op(left, right): # left < right

    if type(left) in (PlusInf, MinusInf) and type(right) in (PlusInf, MinusInf):
        raise CannotCompareError

    if type(left) in [int, float] and type(right) in [int, float]:
        return left < right
    if type(right) == PlusInf:
        return True
    if type(right) == MinusInf:
        return False
    if type(left) == MinusInf:
        return True
    if type(left) == PlusInf:
        return False


    subbed = sub_op(right, left)

    return get_sign(subbed) > 0

def safe_lt_op(left, right):
    try:
        return lt_op(left, right)
    except CannotCompareError:
        return None

def safe_le_op(left, right):
    try:
        return le_op(left, right)
    except CannotCompareError:
        return None

def le_op(left, right): # left <= right

    if type(left) in (int, float) and type(right) in (int, float):
        return left <= right

    if type(left) in (PlusInf, MinusInf) and type(right) in (PlusInf, MinusInf):
        raise CannotCompareError

    if type(right) == PlusInf:
        return True
    if type(right) == MinusInf:
        return False
    if type(left) == MinusInf:
        return True
    if type(left) == PlusInf:
        return False

    subbed = sub_op(right, left)

    return ge_zero(subbed)


def max_op(left, right):
    try:

        if le_op(left, right):
            return right
        else:
            return left

    except CannotCompareError:

        if le_op(right, left):
            return left
        else:
            return right

def safe_max_op(left, right):
    try:
        return max_op(left, right)
    except CannotCompareError:
        return None

def safe_min_op(left, right):
    try:
        return min_op(left, right)
    except CannotCompareError:
        return None

def min_op(left, right):

    if type(left) == PlusInf:
        return right

    if type(right) == PlusInf:
        return left

    if type(left) == MinusInf:
        return left

    if type(right) == MinusInf:
        return right

    try:
        if le_op(left, right):
            return left
        else:
            return right
    except CannotCompareError:
        if le_op(right, left):
            return right
        else:
            return left


def or_op(*args):
    assert len(args) > 1

    res = tuple()

    for r in args:
        if r == 0:
            pass
        elif get_opcode(r) == 'OR':
            assert len(r[1:])>1
            res += r[1:]
        elif r not in res:
            res += (r, )

    if len(res) == 0:
        return 0

    if len(res) == 1:
        return res[0]

    assert len(res)>1

    return ('OR', ) + res

def neg_mask_op(exp, size, offset):
    exp1 = mask_op(exp, size = sub_op(256, add_op(size, offset)), offset = add_op(offset,size))
    exp2 = mask_op(exp, size = offset, offset = 0)

    return or_op(exp1, exp2)

def strategy_concrete(size, offset, shl, exp_size, exp_offset, exp_shl, exp):
    '''
        This is an optimised version of strategy_1, the program would
        work correctly without it, but much slower, since concrete values
        for masks are very common
    '''

    if type(size) == MinusInf:
        outer_left = offset
        outer_right = exp_offset + exp_shl

    elif type(size) == PlusInf:
        outer_left = exp_offset + exp_size + exp_shl
        outer_right = offset

    else:
        outer_left = offset + size
        outer_right = offset

    inner_left = exp_offset + exp_size + exp_shl
    inner_right = exp_offset + exp_shl

    left, right = min(outer_left, inner_left), max(outer_right, inner_right)

    if inner_left <= inner_right:
        return 0
    if inner_left <= outer_right:
        return 0
 
    new_offset = right - exp_shl
    new_size = left - right
    new_shl = shl + exp_shl

    if new_size > 0:
        return mask_op(exp, size=new_size, offset=new_offset, shl=new_shl)
    else:
        return 0

def strategy_0(size, offset, shl, exp_size, exp_offset, exp_shl, exp):
    return 0 if exp == 0 else None

def strategy_1(size, offset, shl, exp_size, exp_offset, exp_shl, exp):
    # default one

    if type(size) == MinusInf: # special case
        outer_left = offset
        outer_right = add_op(exp_offset, exp_shl)
    else:
        outer_left = add_op(offset, size)
        outer_right = offset

    inner_left = add_op(exp_offset, exp_size, exp_shl)
    inner_right = add_op(exp_offset, exp_shl)
    #logprint('left = min',outer_left, '////', inner_left, '==', safe_min_op(outer_left, inner_left))
    #logprint('right = max', outer_right, '////', inner_right, '==', safe_min_op(outer_right, inner_right))

    left, right = safe_min_op(outer_left, inner_left), safe_max_op(outer_right, inner_right)

    if safe_le_op(inner_left, inner_right) is True:
        return 0
    if safe_le_op(inner_left, outer_right) is True:
        return 0
    if safe_le_op(inner_left, inner_right) is True: # hm, duplicate, should be sth else?
        return 0
    if safe_le_op(inner_left, outer_right) is True:
        return 0



    if None not in (left, right):
        new_offset = sub_op(right, exp_shl)
        new_size = sub_op(left, right)
        new_shl = add_op(shl, exp_shl)

        #logprint('new offset', new_offset)
        #logprint('new size', new_size)
        #logprint('new shift', new_shl)
        #logprint()

        gezero = safe_ge_zero(new_size)

        #logprint(gezero)

        if gezero is not False and new_size != 0:
            #logprint('!')
            return mask_op(exp, size=new_size, offset=new_offset, shl=new_shl)

        elif gezero is False or new_size==0:
            return 0

def strategy_2(size, offset, shl, exp_size, exp_offset, exp_shl, exp):
    # move inner left by size, apply mask, and move back 

    return strategy_1(size, sub_op(offset, exp_size), add_op(shl, exp_size), exp_size, exp_offset, sub_op(exp_shl, exp_size), exp)

def strategy_3(size, offset, shl, exp_size, exp_offset, exp_shl, exp):
    # move inner left by it's shl, apply mask, move back

    return strategy_1(size, sub_op(offset, exp_shl), add_op(shl, exp_shl), exp_size, exp_offset, 0, exp)

def strategy_4(size, offset, shl, exp_size, exp_offset, exp_shl, exp):
    # trim left
    tl = strategy_1(MinusInf(), add_op(size,offset), shl, exp_size, exp_offset, exp_shl, exp)

    if tl == 0:
        return 0

    if tl is None or exp != tl[4]:
        return

    # trim right
    tr = strategy_1(PlusInf(), offset, shl, tl[1], tl[2], tl[3], exp)

    return tr

def strategy_final(size, offset, shl, exp_size, exp_offset, exp_shl, exp):

    return ('MASK_SHL', size, offset, shl, ('MASK_SHL', exp_size, exp_offset, exp_shl, exp))


def mask_mask_op(size, offset, shl, exp_size, exp_offset, exp_shl, exp):
    if all_concrete(offset, shl, exp_offset, exp_shl, exp_size) and \
        type(size) in (int, float, MinusInf, PlusInf):
        return strategy_concrete(size, offset, shl, exp_size, exp_offset, exp_shl, exp)

    strategies = (strategy_0, strategy_1, strategy_2, strategy_3, strategy_4, strategy_final)

    for s in strategies:
        res = s(size, offset, shl, exp_size, exp_offset, exp_shl, exp)
        if res is not None:
            logprint(f'{s} success')
            return res

    assert False

mask_dict = {}

def mask_op(exp, size = 256, offset = 0, shl = 0, shr = 0):
    if size == 0:
        return 0

    idx = size, offset, shl, shr, exp
    if idx in mask_dict:
        return mask_dict[idx]

    ret = _mask_op(exp, size, offset, shl, shr)
    mask_dict[idx] = ret
    return ret

def _mask_op(exp, size = 256, offset = 0, shl = 0, shr = 0):

    # if exp == ('DIV', x, 1)
    #        => x
    if get_opcode(exp) == 'DIV' and exp[2] == 1:
        exp = exp[1] # should be done somewhere else, but it's 0:37 at night

    if get_opcode(exp) == 'STORAGE':
        # trimming the storage inside
        
        left = add_op(offset, size)
        right = offset

        stor_shl = exp[2] >> 8
        stor_offset = exp[2] - (stor_shl * 256)
        stor_size = exp[1]

        right = max_op(stor_offset, right)
        left = min_op(stor_offset + stor_size, left)

        stor_offset = right
        stor_size = sub_op(left, right)

        exp = ('STORAGE', stor_size, stor_offset) + exp[3:]

    if get_opcode(exp) == 'OR':

        return or_op( *[mask_op(e, size, offset, shl, shr) for e in exp[1:]])

    if get_opcode(exp) == 'MASK_SHL':
        shl = sub_op(shl, shr)

        double_mask = mask_mask_op(size, offset, shl, exp[1], exp[2], exp[3], exp[4])

        logprint('output:', double_mask)

        return double_mask

    if type(size) != int or size > 0:
        return ('MASK_SHL', size, offset, sub_op(shl,shr), exp)
    else:
        return 0



exp = ('MASK_SHL', 256, 0, -768, 256)
offset =  ('ADD', -256, ('MUL', -8, ('var', 1)))
size = 256
#masked = mask_op(exp, size = PlusInf(), offset = add_op(offset,size))

def apply_mask(val, size, offset=0, shl=0):
    assert (type(val), type(size), type(offset), type(shl)) == (int, int, int, int)

    mask = mask_to_int(size, offset)
    val = val & mask
    if shl>0:
        val = val << shl
    if shl<0:
        val = val >> -shl
    
    return val & mask_to_int(256,0)


#assert masked == ['MASK_SHL', 256, 0, -768, 256]

def try_add(self, other):

#   so proud of this /s

    assert get_opcode(other) == 'MUL'
    assert get_opcode(self) == 'MUL'

    if not len(self) == 3:
        return None
    if not len(other) == 3:
        return None

#    if self, other == MUL(x, exp), MUL(y, exp)
#                   => MUL(x+y, exp)

    if self[2] == other[2]:
        return ('MUL', self[1]+other[1], self[2])



#    if self, other == MUL(x, MASK_SHL(256-y, y, 0, exp)),
#                      MUL(x, MASK_SHL(y, 0, 0, exp))
#                   => MUL(x, (MASK_SHL, 256, 0, 0, exp))

    if self[1] == other[1]:
        self_mask = self[2]
        other_mask = other[2]

        if get_opcode(self_mask) == 'MASK_SHL' and get_opcode(other_mask) == 'MASK_SHL' and\
            self_mask[1]+self_mask[2]==256 and self_mask[2] == other_mask[1] and other_mask[2] == 0 and\
            self_mask[3] == other_mask[3] and self_mask[4] == other_mask[4]:
                return mul_op(self[1], mask_op(self_mask[4], size=256, offset=0, shl=self_mask[3]))


#   if self, other == MUL(x, MASK_SHL(256-y, y, 0, ADD(2**y - 1, MUL(1, exp)))),
#                     MUL(-x, exp)
#                  => MUL(x, 2**y - mask_op(exp, size=y))

    if get_opcode(self[2]) == 'MASK_SHL' and get_opcode(other[2]) != 'MASK_SHL' and self[1] == minus_op(other[1]):
        x = other[2]        
        for y in [3,4,5,6,7,8,16,32,64,128]:
            m = ('MASK_SHL', 256-y, y, 0, ('ADD', 2**y-1, ('MUL', 1, x) ) )# - x #== 2**y-1 - Mask(y,0,0, x)
            if self[2] == m:
                return mul_op(self[1], sub_op(2**y, mask_op(x, size=y)))

    # mask 256,0,0,x - 6,0,0,x == 250,6,0,x

    assert len(self) == 3
    assert len(other) == 3
    assert self[0] == 'MUL'
    assert other[0] == 'MUL'

    self = ('MUL', self[1], self[2])
    other = ('MUL', other[1], other[2])

    if get_opcode(self[2]) != 'MASK_SHL':
        self = ('MUL', self[1], ('MASK_SHL', 256, 0, 0, self[2]))

    if get_opcode(other[2]) != 'MASK_SHL':
        other = ('MUL', other[1], ('MASK_SHL', 256, 0, 0, other[2]))

    if self[2] == other[2]:
        return mul_op(self[1]+other[1], self[2])

    if get_opcode(self[2]) != 'MASK_SHL' or get_opcode(other[2]) != 'MASK_SHL':
        return None

    if self[2][4]!=other[2][4]:
        return None

    if self[2][3] != other[2][3]:
        return None

    if self[2][2] != other[2][2]:
        return None

    if self[2][2] != 0:
        return None


    if self[1] == -other[1]: # self.real == -other.real
        if self[2][1] < other[2][1]:
            self, other = other, self

        assert self[2][1]>other[2][1]

        assert self[2][0] == 'MASK_SHL'

        ret = self[0], self[1], (('MASK_SHL', self[2][1]-other[2][1], other[2][1]) + self[2][3:])

        return ret

    return None

erase_dict = {}

def erase_op(exp, size, shl):
    idx = exp, size, shl
    if idx in erase_dict:
        return erase_dict[idx]

    ret = _erase_op(exp, size, shl)
    erase_dict[idx] = ret
    return ret


def _erase_op(exp, size, shl):
    if get_opcode(exp) == 'OR':
        return or_op( *[erase_op(e, size, shl) for e in exp[1:]] )
    
    ret = or_op( mask_op(exp, size = PlusInf(), offset = add_op(shl,size)), mask_op(exp, offset = shl, size = MinusInf()))
    return ret
