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
import sim 
import utils

block_height = 5

number = 42
ticket, puzzhash = helpers.get_ticket(number, block_height)
assert  puzzhash == ticket.get_tree_hash()

alice: Wallet = sim.network.make_wallet("alice")
sim.farm(farmer=alice)

mojos = 1_000
coin = sim.launch_smart_coin(alice, ticket, mojos)
assert coin != None

print(coin)

sim.end()
