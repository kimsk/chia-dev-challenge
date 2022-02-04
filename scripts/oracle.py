# test oracle
# src/oracle.clsp

import sys
sys.path.insert(0, "../drivers")

from blspy import (PrivateKey, AugSchemeMPL, G1Element, G2Element)

from cdv.test import Wallet
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from typing import List, Tuple

import helpers
import utils

block_height = 5
oracle, oracle_puzzhash = helpers.get_oracle(block_height)

utils.print_sexp(oracle)

winning_number = 42
solution = Program.to([winning_number])
result = oracle.run(solution)
utils.print_sexp(result)
