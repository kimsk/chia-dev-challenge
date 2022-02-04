from blspy import (PrivateKey, AugSchemeMPL, G1Element, G2Element)
from cdv.util.load_clvm import load_clvm
from chia.types.blockchain_format.program import Program
from chia.types.blockchain_format.sized_bytes import bytes32

from typing import List, Optional, Tuple

# each ticket costs thousand mojos
TICKET_COST = 1_000

# Secret Key: 5a3e6dc5d972fdbdfdfd9992ed060023a835521453fb5def460ca121e9e8fdc0
# Public Key: b4de387ca32dfea3fda2e415597e53d0b155647861a80ba61687a15f2f37875a8991911f320b882cd5523be4e259b81b
# Fingerprint: 1071225497
# HD Path: m
APPROVER_SK: PrivateKey = PrivateKey.from_bytes(bytes.fromhex("5a3e6dc5d972fdbdfdfd9992ed060023a835521453fb5def460ca121e9e8fdc0"))
APPROVER_PK: G1Element = APPROVER_SK.get_g1()
GENESIS_ORACLE: Program = load_clvm(
        "../clsp/oracle.clsp", 
        package_or_requirement=__name__, search_paths=["../include"]
    ).curry(APPROVER_PK)

def get_oracle(block_height) -> Tuple[Program, bytes32]:
    oracle = GENESIS_ORACLE.curry(block_height)
    return oracle, oracle.get_tree_hash()

# Secret Key: 470f15761af389ad5fd8f8514ef189a577f929b73649b45a685f336b4c6f2a0d
# Public Key: 8ff3841502d3b257be33b43934dc9f3a3f62a648149d01b52d68ddef9e14156e05e38aa00e553caa900648007c06a30c
# Fingerprint: 2474242265
# HD Path: m
MEGA_MOJOS_SK: PrivateKey = PrivateKey.from_bytes(bytes.fromhex("470f15761af389ad5fd8f8514ef189a577f929b73649b45a685f336b4c6f2a0d"))
MEGA_MOJOS_PK: G1Element = MEGA_MOJOS_SK.get_g1()
MEGA_MOJOS_FEE = 0.1

VALID_NUMBER_RANGES = range(0, 100)

def get_genesis_ticket(oracle_puzzhash, number, block_height) -> Program:
    ticket: Program = load_clvm(
        "../clsp/ticket.clsp", 
        package_or_requirement=__name__, search_paths=["../include"]
    ).curry(
        MEGA_MOJOS_PK, 
        oracle_puzzhash,
        number
    )
    return ticket

def get_ticket(oracle_puzzhash, number, block_height) -> Optional[Tuple[Program, bytes32]]:
    if (number not in VALID_NUMBER_RANGES):
        return None
    ticket: Program = get_genesis_ticket(oracle_puzzhash, number, block_height).curry(
        block_height
    )
    return ticket, ticket.get_tree_hash()

def generate_tickets(oracle_puzzhash, block_height) -> List[Tuple[Program, bytes32]]:
    return [
        get_ticket(oracle_puzzhash, number, block_height)
            for number in VALID_NUMBER_RANGES
    ]
