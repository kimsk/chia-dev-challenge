import math
import sys
sys.path.insert(0, "../drivers")

from blspy import (AugSchemeMPL, G2Element)

from cdv.test import Wallet
from cdv.util.load_clvm import load_clvm
from chia.consensus.default_constants import DEFAULT_CONSTANTS
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.coin_spend import CoinSpend
from chia.types.spend_bundle import SpendBundle
from chia.util.hash import std_hash
from clvm.casts import int_to_bytes

import helpers
import sim

# Prepare Wallet
print("1) Preparing wallets for Alice, Bob, and Charlie.")

mega_mojos: Wallet = sim.network.make_wallet("mega_mojos")
alice: Wallet = sim.network.make_wallet("alice")
bob: Wallet = sim.network.make_wallet("bob")
charlie: Wallet = sim.network.make_wallet("charlie")
sim.farm(farmer=mega_mojos)
sim.farm(farmer=alice)
sim.farm(farmer=bob)
sim.farm(farmer=charlie)

print(f'\talice balance:\t\t{alice.balance()}')
print(f'\tbob balance:\t\t{bob.balance()}')
print(f'\tcharlie balance:\t{charlie.balance()}')
input("...\n")

# Drawing Info
block_height = 15
oracle, oracle_puzzhash = helpers.get_oracle(block_height)
possible_tickets = helpers.generate_tickets(oracle_puzzhash, block_height)
print(f"2) MegaMojos prepares drawing for block # {block_height} (current block: {sim.get_block_height()}).")
print(f'\tOracle puzzle is created: {oracle_puzzhash}')
print(f'\t{len(possible_tickets)} puzzles for tickets prepared.')
input("...\n")

# Buying Lottery
print(f"3) Alice, Bob, and Charlie buy lottery tickets (1000 mojos per ticket).")
def buy_ticket(wallet: Wallet, number, block_height):
    ticket, _ = helpers.get_ticket(oracle_puzzhash, number, block_height)
    coin = sim.launch_smart_coin(wallet, ticket, helpers.TICKET_COST)
    return ticket, coin

_, alice_coin = buy_ticket(alice, 5, block_height)
_, alice_coin2 = buy_ticket(alice, 42, block_height)
_, bob_coin = buy_ticket(bob, 42, block_height)
_, bob_coin2 = buy_ticket(bob, 52, block_height)
_, charlie_coin = buy_ticket(charlie, 26, block_height)
tickets = [alice_coin, alice_coin2, bob_coin, bob_coin2, charlie_coin]
print(f"\t{len(tickets)} tickets bought...")
for t in tickets:
    print(f"\t\t{t.puzzle_hash}")

print(f'\n\talice balance:\t\t{alice.balance()}')
print(f'\tbob balance:\t\t{bob.balance()}')
print(f'\tcharlie balance:\t{charlie.balance()}')

input("...\n")

print(f"4) Waiting until block height reaches: # {block_height}.")
# until block height reaches
while (sim.get_block_height() < block_height):
    sim.pass_blocks(1)
    print(f"\tblock height: {sim.get_block_height()}")

winning_number = 42
_, winning_ticket_puzzhash = helpers.get_ticket(oracle_puzzhash, winning_number, block_height)
print(f"\n\tAnnounce winning number: {winning_number}")
print(f"\tWinning ticket puzzle hash: {winning_ticket_puzzhash}")

oracle_coin = sim.launch_smart_coin(mega_mojos, oracle, 1)
print(f"\tOracle coin created: {oracle_coin.puzzle_hash}")
input("...\n")

print(f"5) Looking for winning and losing tickets.")
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

print(f"\t{len(winning_tickets)} winning tickets found.")
for t in winning_tickets:
    print(f"\t\t{t.coin.puzzle_hash}")
print(f"\t{len(losing_tickets)} losing tickets found.")
for t in losing_tickets:
    print(f"\t\t{t.coin.puzzle_hash}")

# find winning amount
total_amount = sum(t.coin.amount for t in all_tickets)

winning_amount = math.floor(
    (total_amount * (1 - helpers.MEGA_MOJOS_FEE))
    / len(winning_tickets))

print(f"\n\ttotal amount: {total_amount} mojos")
print(f"\twinning amount for each winning ticket: {winning_amount} mojos")

input("...\n")

print(f"6) Prepare spend bundle.")

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
print(f"\tapprover signature: {approver_sig}")
print(f"\tmega mojos signature: {mega_mojos_sig}")

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
print(f"\t{len(spends)} coins in the spend bundle.")
input("...\n")

print(f"7) Push spend bundle.")

result = sim.push_tx(spend_bundle)
print(f'\talice balance:\t\t{alice.balance()}')
print(f'\tbob balance:\t\t{bob.balance()}')
print(f'\tcharlie balance:\t{charlie.balance()}')

sim.end()
