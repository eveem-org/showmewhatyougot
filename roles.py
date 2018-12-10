from trace import walk_exp
from helpers import opcode

from collections import defaultdict


class Role:
    def __init__(self, name=None, definition=None):
        self.name = name
        self.definition = definition
        self.setters = list()
        self.funcs = set()
        self.withdrawals = set()
        self.calls = set()
        self.destructs = set()
        self.destructs_init = set()

class Roles(defaultdict):
    '''
        a dictionary of roles, indexed by either a definition, or a name, 
        if definition is not available
        
        e.g.
        (STORAGE, 160, 0, 1): Role()
        (STORAGE, 160, 0, 2): Role()
        'anyone': Role()

    '''


    def __missing__(self, key):
        self[key] = Role(name=key)
        return self[key]

    def __init__(self, functions, stor_defs):
        super(Roles, self).__init__()

        '''
            create roles for each storage_def that is an address

        '''

        for s, name in stor_defs.items():
            # s: (STORAGE, 160, 0, _) => add_role(name, s)
            if s[:3] == ('STORAGE', 160, 0) and len(s) == 4:
                self[s] = Role(name=name, definition=s)

        '''
            create roles for every other storage used by contract,
            even if we cannot find a getter, name for it

        '''

        def find_storages(exp):
            if opcode(exp) == 'STORAGE':
                return exp

            if opcode(exp) == 'STORE':
                return ('STORAGE', ) + exp[1:4]

        for f in functions.values():
            trace = f['trace']
            storages = walk_exp(trace, find_storages)
            for s in storages:
                # def: (STORAGE, 160, 0, stor_num) => add_role('stor_{stor_num}', def)
                if len(s) == 4 and s[:3] == ('STORAGE', 160, 0) and s not in self:
                    self[s] = Role(name=f'stor_{s[3]}', definition=s)

