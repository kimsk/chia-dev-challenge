# test buying ticket
# src/ticket.clsp

import sys
sys.path.insert(0, "../drivers")

from cdv.test import Wallet
from cdv.util.load_clvm import load_clvm
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from typing import List, Tuple

import helpers
import utils

block_height = 5

# valid number
number = 42
ticket, puzzhash = helpers.get_ticket(number, block_height)
assert  puzzhash == ticket.get_tree_hash()

utils.print_sexp(ticket)

# invalid number
assert None == helpers.get_ticket(100, block_height)


# win
player_puzzle_hash = "0xcafef00d"
winning_number = 42
winning_amount = 1_000_000
solution = Program.to([
    winning_number, 
    player_puzzle_hash, 
    winning_amount])
result = ticket.run(solution)
utils.print_sexp(result)

# not win
solution = Program.to([
    0, 
    [], 
    []])
result = ticket.run(solution)
utils.print_sexp(result)
