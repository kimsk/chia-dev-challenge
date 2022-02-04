from chia.types.blockchain_format.coin import Coin
from clvm import SExp
from clvm_tools import binutils
import json

def print_json(dict):
    print(json.dumps(dict, sort_keys=True, indent=4))

def print_sexp(sexp: SExp):
    print(binutils.disassemble(sexp))

def print_coin(coin: Coin):
    print_json(coin.to_json_dict())
