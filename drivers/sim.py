import asyncio
from blspy import (PrivateKey, AugSchemeMPL, G1Element, G2Element)

from cdv.test import Network, Wallet
from chia.consensus.default_constants import DEFAULT_CONSTANTS
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.types.coin_spend import CoinSpend
from chia.types.condition_opcodes import ConditionOpcode
from chia.types.spend_bundle import SpendBundle

from chia.wallet.puzzles.p2_delegated_puzzle_or_hidden_puzzle import DEFAULT_HIDDEN_PUZZLE_HASH, calculate_synthetic_secret_key, puzzle_for_public_key_and_hidden_puzzle_hash

network: Network = asyncio.run(Network.create())
asyncio.run(network.farm_block())

def farm(farmer: Wallet):
    asyncio.run(network.farm_block(farmer=farmer))

def get_coin(wallet: Wallet, amt, fee=0):
    return asyncio.run(wallet.choose_coin(amt + fee))

def push_tx(spend_bundle: SpendBundle):
    result = asyncio.run(network.push_tx(spend_bundle))
    return result

def launch_smart_coin(wallet: Wallet, puzzle: Program, amt):
    return asyncio.run(wallet.launch_smart_coin(puzzle, amt=amt))

def end():
    asyncio.run(network.close())

def get_coins_by_puzzle_hash(
        puzzle_hash, 
        include_spent_coins = True,
        end_height = None):
    return asyncio.run(network.sim_client.get_coin_records_by_puzzle_hash(
        puzzle_hash, 
        include_spent_coins=include_spent_coins,
        end_height=end_height
        ))

def get_coin_by_coin_id(coin_id: bytes32):
    return asyncio.run(network.sim_client.get_coin_record_by_name(coin_id))

def get_block_height():
    return network.sim.get_height()

def get_block_record_by_height(height):
    return asyncio.run(network.sim_client.get_block_record_by_height(height))

def pass_blocks(number):
    network.sim.pass_blocks(number)

def get_normal_coin_spend(wallet: Wallet, coin, conditions):
    assert coin != None

    delegated_puzzle_solution = Program.to((1, conditions))
    synthetic_sk: PrivateKey = calculate_synthetic_secret_key(
        wallet.sk_,
        DEFAULT_HIDDEN_PUZZLE_HASH
    )
    synthetic_pk = synthetic_sk.get_g1()

    solution = Program.to([[], delegated_puzzle_solution, []])

    coin_spend = CoinSpend(
            coin.as_coin(),
            wallet.puzzle, # p2_delegated_puzzle_or_hidden_puzzle
            solution,
        )

    sig_msg = delegated_puzzle_solution.get_tree_hash() + coin.name() + DEFAULT_CONSTANTS.AGG_SIG_ME_ADDITIONAL_DATA
    sig = AugSchemeMPL.sign(synthetic_sk, sig_msg)

    return coin_spend, sig_msg, sig, synthetic_pk
