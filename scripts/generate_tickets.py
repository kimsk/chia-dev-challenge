# test buying ticket
# src/ticket.clsp

import sys
sys.path.insert(0, "../drivers")

from cdv.test import Wallet
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from typing import List, Tuple

import helpers
import utils

block_height = 5
tickets: List[Tuple[Program, bytes32]] = helpers.generate_tickets(block_height)

for number in helpers.VALID_NUMBER_RANGES:
    ticket, puzzhash = tickets[number]
    assert ticket.get_tree_hash() == puzzhash
    utils.print_sexp(ticket)
