# Quantum Leap: PoS Validator Node Simulator

## Concept

This project is a Python-based simulation of a validator node's lifecycle within a simplified Proof-of-Stake (PoS) blockchain network. It serves as an educational tool to demonstrate the core concepts of a PoS consensus mechanism, including stake-based leader selection, block proposal, validation, and consensus achievement.

The simulation abstracts away complex cryptographic and networking layers to focus on the architectural patterns and state transitions that define a PoS system. It utilizes external libraries like `web3.py` for hashing, `requests` to simulate fetching data from external sources (like a transaction mempool API), and `Faker` to generate realistic test data.

## Code Architecture

The simulator is built using an object-oriented approach, with distinct classes representing different components of the blockchain ecosystem.

```
+---------------------------+
| PoSConsensusSimulator     | (Orchestrator)
+---------------------------+
| - validators: List[ValidatorNode]
| - blockchain: Blockchain
| - mempool: List[Transaction]
|---------------------------|
| + run_simulation_round()  |
| + _select_leader()        |
| + _fetch_mock_transactions()|
+---------------------------+
         |                         ^
         | manages                 | contains
         v                         |
+---------------------------+      +---------------------------+
| ValidatorNode             |----->| Blockchain                |
+---------------------------+      +---------------------------+
| - address: str            |      | - chain: List[Block]      |
| - stake: float            |      |---------------------------|
|---------------------------|      | + add_block(block)        |
| + propose_block()         |      | + is_block_valid(block)   |
| + validate_block()        |      +---------------------------+
+---------------------------+               ^
                                          | contains
                                          v
                         +---------------------------+      +---------------------------+
                         | Block                     |----->| Transaction               |
                         +---------------------------+      +---------------------------+
                         | - index: int              |      | - sender: str             |
                         | - transactions: List[Tx]  |      | - receiver: str           |
                         | - previous_hash: str      |      | - amount: float           |
                         | - hash: str               |      +---------------------------+
                         +---------------------------+
```

*   **`Transaction`**: A simple data class representing a transaction with a sender, receiver, and amount.
*   **`Block`**: Represents a block containing metadata (index, timestamp, validator address) and a list of transactions. It includes a `calculate_hash()` method that uses `Web3.keccak` for authenticity.
*   **`Blockchain`**: Manages the list of blocks (the chain). It is responsible for adding new blocks and performing fundamental validation checks (e.g., checking the `previous_hash`).
*   **`ValidatorNode`**: The core component representing a participant in the network. Each node has a unique address and a specific amount of stake. It can `propose_block()` when selected as a leader and `validate_block()` when receiving a proposal from a peer.
*   **`PoSConsensusSimulator`**: The main orchestrator class. It initializes the network with a set of validators, manages the global state (like the mempool), runs the consensus rounds, and implements the stake-weighted leader selection logic.

## How it Works

The simulation proceeds in discrete rounds, where each round aims to produce and confirm one new block.

1.  **Initialization**: The `PoSConsensusSimulator` is created with a specified number of validators. Each validator is assigned a unique address and a randomized initial stake.

2.  **Populate Mempool**: At the start of a round, the simulator checks if the transaction mempool is low. If so, it calls `_fetch_mock_transactions()`, which simulates fetching pending transactions by making a real HTTP request to a public mock API (`jsonplaceholder.typicode.com`). This demonstrates handling external dependencies and potential failures (with a fallback to local data generation).

3.  **Leader Selection**: A leader (or "block proposer") for the current round is chosen using a weighted random selection algorithm. The probability of a validator being chosen is directly proportional to its stake (`validator.stake / total_stake`).

4.  **Block Proposal**: The selected leader pulls a set of transactions from the mempool and creates a new `Block`. This block contains the transactions, a new index, and the hash of the previous block in the chain.

5.  **Validation & Voting**: The proposed block is broadcast to all other validators in the network. Each validator independently runs `validate_block()`, which checks the block's integrity against its local copy of the blockchain.

6.  **Consensus Check**: The simulator tallies the "votes." The weight of each vote is equal to the validator's stake. If the total stake of validators who approved the block meets or exceeds a predefined threshold (e.g., 2/3 of the total network stake), consensus is reached.

7.  **Chain Append**: If consensus is achieved, the new block is officially added to the `Blockchain` instance. The transactions included in that block are then removed from the mempool.

8.  **Repeat**: The process repeats for the next round, starting again with leader selection.

## Usage

To run the simulation, you first need to install the required dependencies.

1.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the simulation:**

    You can run the main script directly, which is configured to run a simulation with 10 validators for 5 rounds.

    ```bash
    python main.py
    ```

    Alternatively, you can import and use the simulator class in your own script.

    ```python
    from pos_simulator import PoSConsensusSimulator

    # Initialize the simulator with 10 validators
    simulator = PoSConsensusSimulator(num_validators=10)

    # Run the simulation for 5 consensus rounds
    simulator.run_simulation(num_rounds=5)

    # Print the final state of the blockchain
    simulator.print_blockchain()
    ```

3.  **Example Output:**

    You will see a detailed log of the simulation process, showing leader selection, block proposals, consensus results, and the final state of the blockchain.

    ```
    INFO:root:Validator 0x...A1B2 initialized with stake: 1203.45
    INFO:root:Validator 0x...C3D4 initialized with stake: 987.65
    ...

    --- Starting Consensus Round for Block #1 ---
    INFO:root:Fetching 7 mock transactions from external API...
    INFO:root:Successfully added 7 new transactions to the mempool.
    INFO:root:Leader for round #1 selected: 0x...A1B2 (Stake: 1203.45)
    INFO:root:Validator 0x...A1B2 PROPOSES Block(#1 | Val: ...A1B2 | Txs: 5 | Hash: ...e4f5)
    INFO:root:Consensus check: Approving stake 10500.00/10500.00
    INFO:root:CONSENSUS REACHED. Block(#1 | Val: ...A1B2 | Txs: 5 | Hash: ...e4f5) added to the chain.

    --- Blockchain State ---
      -> Block(#0 | Val: SYSTEM_GENESIS | Txs: 0 | Hash: ...1a2b)
      -> Block(#1 | Val: ...A1B2 | Txs: 5 | Hash: ...e4f5)
    ------------------------

    ...
    ```