from eth_typing import (
    Address,
    Hash32
)
from eth_utils import denoms


precompiled = {
    1: "erecover", # msg_hash =, v = , r = , s =
    2: "sha256hash",
    3: "ripemd160hash",
    #4: "memcpy", -- handled separately
    5: "bigModExp",
    6: "bn256Add",
    7: "bn256ScalarMul",
    8: "bn256Pairing",
}

precompiled_var_names = {
    1: "signer",
    2: "hash",
    3: "hash",
    #4: "memcpy", -- handled separately
    5: "mod_exp",
    6: "bn_add",
    7: "bn_scalar_mul",
    8: "bn_pairing",
}

ANY = 'any'
UINT256 = 'uint256'
BYTES = 'bytes'

UINT_256_MAX = 2**256 - 1
UINT_256_CEILING = 2**256
UINT_255_MAX = 2**255 - 1
UINT_255_CEILING = 2**255
UINT_255_NEGATIVE_ONE = -1 + UINT_256_CEILING
NULL_BYTE = b'\x00'
EMPTY_WORD = NULL_BYTE * 32

UINT_160_CEILING = 2**160
