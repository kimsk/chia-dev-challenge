> # For Clovyr Chia Developer Challenge, please review this [tag](https://github.com/kimsk/chia-dev-challenge/tree/clovyr-challenge-eligible).

# Mega Mojos :seedling:

## Overview

A lottery game like **Mega Millions** or **Powerball** simulated on Chia Blockchain.


## Idea

1. A player buy ticket by selecting a number from 0-99 and send 1000 mojos to a ticket smart coin.
2. Each ticket smart coin puzzle curries in
    - `PK`: the lottery official has the `SK` to sign the spend.
    - `ORACLE_PUZZLE_HASH`: oracle that announce the same winning number and block height has to be spent together.
    - `NUMBER`: a selected number.
    - `BLOCK_HEIGHT`: each drawing has to happen after this block height (time simulation). 
3. Once the blockchain reaches the specific block height, the winning number is announced. The lottery offical will gather all tickets and spend them together with the oracle.
4. The lottery offical will take 10% cut and divide the rest to winners who pick the correct number.
5. If there is no winner, the whole reward will be given to the fabulous Chia farmer :farmer:.

## Chialisp

### [Oracle](./clsp/oracle.clsp)
```lisp
(mod 
    (
        APPROVER_PK 
        BLOCK_HEIGHT 
        winning_number
    )

    (include condition_codes.clib)

    (list
        (list AGG_SIG_ME APPROVER_PK (sha256 BLOCK_HEIGHT winning_number))
        (list CREATE_PUZZLE_ANNOUNCEMENT (sha256 (q . "block_height") BLOCK_HEIGHT))
        (list CREATE_PUZZLE_ANNOUNCEMENT (sha256 (q . "winning_number") winning_number))
    )
)
```
When the oracle is spent, it will announce `block height` and `winning number` which all tickets will have to verify. The approver of the lottery official has to sign the spend too.

> The approver has to be different key from the official who sign the spend for tickets.)

### [Ticket](./clsp/ticket.clsp)
```lisp
(mod (
        PK 
        ORACLE_PUZZLE_HASH 
        NUMBER 
        BLOCK_HEIGHT 
        winning_number 
        player_puzzle_hash 
        winning_amount
    )
    
    (include condition_codes.clib)

    ; if this is winning ticket, also CREATE_COIN to the ticket owner
    (defun-inline possibly_winner 
        (
            PK 
            NUMBER 
            player_puzzle_hash 
            winning_amount 
            conditions
        )
        (if (= NUMBER winning_number)
            (c 
                (list CREATE_COIN player_puzzle_hash winning_amount)
                conditions
            )
            conditions
        )
    )
    
    ; main
    (possibly_winner
        PK
        NUMBER
        player_puzzle_hash
        winning_amount
        (list
            (list AGG_SIG_ME PK (sha256 winning_number winning_amount))
            (list ASSERT_HEIGHT_ABSOLUTE BLOCK_HEIGHT)
            (list ASSERT_PUZZLE_ANNOUNCEMENT (sha256 ORACLE_PUZZLE_HASH (sha256 (q . "block_height") BLOCK_HEIGHT)))
            (list ASSERT_PUZZLE_ANNOUNCEMENT (sha256 ORACLE_PUZZLE_HASH (sha256 (q . "winning_number") winning_number)))
        )
    )
)
```
A ticket is differentiated by `number` and `block height`. For example, if alice buys a ticket with number `42` and block height `101`, next drawing, the block height will be different, so even if the number is the same, the puzzle hash will noto be the same.

```lisp
(
        PK 
        ORACLE_PUZZLE_HASH 
        NUMBER 
        BLOCK_HEIGHT
        ...
    )
```

The ticket puzzle checks the selected `NUMBER` and the `winning_number`. If they match, `CREATE_COIN` condition with the `winning_amount` (provided by the lottery official) to the puzzle hash of the original ticket buyer. 

`(CREATE_COIN player_puzzle_hash winning_amount)`

To make sure the ticket coin is not spent by any malicious user :ninja:, it will verify signature and annoucements.

```lisp
(AGG_SIG_ME PK (sha256 winning_number winning_amount))
(ASSERT_HEIGHT_ABSOLUTE BLOCK_HEIGHT)
(ASSERT_PUZZLE_ANNOUNCEMENT (sha256 ORACLE_PUZZLE_HASH (sha256 (q . "block_height") BLOCK_HEIGHT)))
(ASSERT_PUZZLE_ANNOUNCEMENT (sha256 ORACLE_PUZZLE_HASH (sha256 (q . "winning_number") winning_number)))
```

## Testings

-[oracle](./scripts/oracle.py)
-[buying ticket](./scripts/buy_ticket.py)
-[winners](./script/sim_winning_tickets.py)
-[sim_no_winners.py](./script/sim_no_winners.py)
