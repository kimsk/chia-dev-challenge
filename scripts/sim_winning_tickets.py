import math
import sys
sys.path.insert(0, "../drivers")

from blspy import (PrivateKey, AugSchemeMPL, G1Element, G2Element)

from cdv.test import Wallet
from cdv.util.load_clvm import load_clvm
from chia.consensus.default_constants import DEFAULT_CONSTANTS
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.coin_spend import CoinSpend
from chia.types.spend_bundle import SpendBundle
from chia.util.hash import std_hash
from clvm.casts import int_to_bytes
from typing import List, Tuple

import helpers
import sim
import utils

# drawing info
block_height = 10
oracle, oracle_puzzhash = helpers.get_oracle(block_height)
possible_tickets = helpers.generate_tickets(oracle_puzzhash, block_height)

# mega_mojos
mega_mojos: Wallet = sim.network.make_wallet("mega_mojos")
sim.farm(farmer=mega_mojos)
# 3 players, alice, bob, and charlie
alice: Wallet = sim.network.make_wallet("alice")
sim.farm(farmer=alice)
bob: Wallet = sim.network.make_wallet("bob")
sim.farm(farmer=bob)
charlie: Wallet = sim.network.make_wallet("charlie")
sim.farm(farmer=charlie)

print(f'alice balance: {alice.balance()}')
print(f'bob balance: {bob.balance()}')
print(f'charlie balance: {charlie.balance()}')


def buy_ticket(wallet: Wallet, number, block_height):
    ticket, _ = helpers.get_ticket(oracle_puzzhash, number, block_height)
    coin = sim.launch_smart_coin(wallet, ticket, helpers.TICKET_COST)
    return ticket, coin

# buy 4 tickets
_, alice_coin = buy_ticket(alice, 5, block_height)
_, alice_coin2 = buy_ticket(alice, 15, block_height)
_, bob_coin = buy_ticket(bob, 15, block_height)
_, bob_coin = buy_ticket(bob, 52, block_height)
_, charlie_coin = buy_ticket(charlie, 26, block_height)


# _, alice_coin2 = buy_ticket(alice, 15, block_height)

print("tickets bought")
print(f'alice balance: {alice.balance()}')
print(f'bob balance: {bob.balance()}')
print(f'charlie balance: {charlie.balance()}')


# until block height reaches
while (sim.get_block_height() < block_height):
    sim.pass_blocks(1)
    print(sim.get_block_height())

# winning number announced
# create oracle when we have winning number
winning_number = 15
_, winning_ticket_puzzhash = helpers.get_ticket(oracle_puzzhash, winning_number, block_height)
# oracle = oracle.curry(winning_number)
oracle_coin = sim.launch_smart_coin(mega_mojos, oracle, 1)

# look for winning and losing tickets
winning_tickets = []
losing_tickets = []
all_tickets = []
puzzhash_to_puzzles = {}
for ticket, puzzhash in possible_tickets:
    found = sim.get_coins_by_puzzle_hash(
        puzzle_hash = puzzhash,
        include_spent_coins = False,
        end_height = block_height)
    
    if (len(found) > 0):
        puzzhash_to_puzzles[puzzhash.hex()] = ticket
        all_tickets.extend(found)
        if (winning_ticket_puzzhash == puzzhash):
            winning_tickets.extend(found)
        else:
            losing_tickets.extend(found)

# assert len(all_tickets) == 5
# assert len(winning_tickets) == 2
# assert len(losing_tickets) == 3
print(losing_tickets)
print(winning_tickets)


# find winning amount
total_amount = sum(t.coin.amount for t in all_tickets)

winning_amount = math.floor(
    (total_amount * (1 - helpers.MEGA_MOJOS_FEE))
    / len(winning_tickets))
# assert total_amount == 5000
# assert winning_amount == 2250

# prepare spends
spends = []
mega_mojos_sig = G2Element()

for t in all_tickets:
    parent_coin_id = t.coin.parent_coin_info
    parent_coin_puzzle_hash = sim.get_coin_by_coin_id(parent_coin_id).coin.puzzle_hash
    solution = Program.to([
        winning_number, 
        parent_coin_puzzle_hash, 
        winning_amount
    ])
    spend = CoinSpend(
        t.coin,
        puzzhash_to_puzzles[t.coin.puzzle_hash.hex()],
        solution
    )
    spends.append(spend)
    sig = AugSchemeMPL.sign(
        helpers.MEGA_MOJOS_SK,
        std_hash(int_to_bytes(winning_number) + int_to_bytes(winning_amount))
        + t.coin.name()
        + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA 
    )
    mega_mojos_sig = AugSchemeMPL.aggregate([mega_mojos_sig, sig])

oracle_spend = CoinSpend(
    oracle_coin,
    oracle,
    Program.to([winning_number])
)
spends.append(oracle_spend)

approver_sig = AugSchemeMPL.sign(
    helpers.APPROVER_SK,
    std_hash(int_to_bytes(block_height) + int_to_bytes(winning_number))
    + oracle_coin.name()
    + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA
)
print(approver_sig)
print(mega_mojos_sig)

agg_sig = AugSchemeMPL.aggregate(
    [
        approver_sig, 
        mega_mojos_sig
    ]
)

spend_bundle = SpendBundle(
    spends,
    agg_sig
)

result = sim.push_tx(spend_bundle)
print(result)

print("winning number announced")
print(f'alice balance: {alice.balance()}')
print(f'bob balance: {bob.balance()}')
print(f'charlie balance: {charlie.balance()}')


sim.end()

utils.print_json(spend_bundle.to_json_dict(include_legacy_keys = False, exclude_modern_keys = False))
