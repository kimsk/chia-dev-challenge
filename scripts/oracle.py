# test oracle
# src/oracle.clsp

import sys
sys.path.insert(0, "../drivers")

from blspy import (PrivateKey, AugSchemeMPL, G1Element, G2Element)

from cdv.test import Wallet
from chia.consensus.default_constants import DEFAULT_CONSTANTS
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.coin_record import Coin
from chia.types.coin_spend import CoinSpend
from chia.types.spend_bundle import SpendBundle
from chia.util.hash import std_hash
from clvm.casts import int_to_bytes
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
message = std_hash(int_to_bytes(block_height) + int_to_bytes(winning_number))
coin = Coin(
        bytes.fromhex("2f7edc65d5844b8f320aea02fd147f95ecb0737b2be5fdb2e3105cdc7917a974"), 
        oracle_puzzhash, 
        10)
sig = AugSchemeMPL.sign(
    helpers.APPROVER_SK,
    message
    + coin.name()
    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA


    )
spend_bundle = SpendBundle(
    [
        CoinSpend(
            coin,
            oracle,
            solution
        )
    ],
    sig
)

AugSchemeMPL.verify(helpers.APPROVER_PK, message, sig)
utils.print_json(spend_bundle.to_json_dict(include_legacy_keys = False, exclude_modern_keys = False))
