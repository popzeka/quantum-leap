import hashlib
import json
import random
import time
from typing import List, Dict, Any, Optional
import logging

import requests
from faker import Faker
from web3 import Web3

# --- Configuration ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize Faker for generating mock data
fake = Faker()

# --- Core Data Structures ---

class Transaction:
    """
    Represents a simple transaction in the blockchain.
    In a real system, this would be cryptographically signed.
    """
    def __init__(self, sender: str, receiver: str, amount: float, data: Dict[str, Any] = None):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.data = data or {}
        self.timestamp = time.time()

    def to_dict(self) -> Dict[str, Any]:
        """Converts the transaction to a dictionary for serialization."""
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'data': self.data,
            'timestamp': self.timestamp,
        }

    def __str__(self) -> str:
        return f"TX({self.sender[-6:]} -> {self.receiver[-6:]}: {self.amount})"


class Block:
    """
    Represents a block in the blockchain, containing transactions and metadata.
    """
    def __init__(self, index: int, transactions: List[Transaction], previous_hash: str, validator: str):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.validator = validator
        self.hash = self.calculate_hash()

    def calculate_hash(self) -> str:
        """
        Calculates the SHA-256 hash of the block.
        Uses web3.py's Keccak implementation for a more authentic blockchain feel.
        """
        block_string = json.dumps(
            {
                'index': self.index,
                'timestamp': self.timestamp,
                'transactions': [tx.to_dict() for tx in self.transactions],
                'previous_hash': self.previous_hash,
                'validator': self.validator,
            },
            sort_keys=True
        ).encode()
        return Web3.keccak(block_string).hex()

    def __str__(self) -> str:
        return f"Block(#{self.index} | Val: {self.validator[-6:]} | Txs: {len(self.transactions)} | Hash: {self.hash[-6:]})"


class Blockchain:
    """
    Manages the chain of blocks, including validation and addition.
    This is a simplified, shared-state representation of the distributed ledger.
    """
    def __init__(self):
        self.chain: List[Block] = []
        self._create_genesis_block()

    def _create_genesis_block(self):
        """Creates the very first block in the chain."""
        genesis_block = Block(index=0, transactions=[], previous_hash="0"*64, validator="SYSTEM_GENESIS")
        self.chain.append(genesis_block)

    @property
    def last_block(self) -> Block:
        """Returns the most recent block in the chain."""
        return self.chain[-1]

    def add_block(self, block: Block) -> bool:
        """
        Adds a new block to the chain after validating it.
        Args:
            block (Block): The block to be added.
        Returns:
            bool: True if the block was successfully added, False otherwise.
        """
        if self.is_block_valid(block, self.last_block):
            self.chain.append(block)
            return True
        return False

    def is_block_valid(self, block: Block, previous_block: Block) -> bool:
        """
        Validates a block based on several criteria.
        1. Index must be sequential.
        2. Previous hash must match.
        3. The block's calculated hash must be correct.
        """
        if block.index != previous_block.index + 1:
            logging.warning(f"Invalid index: Expected {previous_block.index + 1}, got {block.index}")
            return False
        if block.previous_hash != previous_block.hash:
            logging.warning(f"Invalid previous hash for block #{block.index}")
            return False
        if block.hash != block.calculate_hash():
            logging.warning(f"Invalid block hash for block #{block.index}")
            return False
        return True


# --- Validator and Consensus Logic ---

class ValidatorNode:
    """
    Represents a single validator in the Proof-of-Stake network.
    """
    def __init__(self, address: str, stake: float, blockchain: Blockchain):
        self.address = address
        self.stake = stake
        self.blockchain = blockchain
        logging.info(f"Validator {self.address[-8:]} initialized with stake: {self.stake}")

    def propose_block(self, transactions: List[Transaction]) -> Block:
        """
        Creates and proposes a new block if this validator is the chosen leader.
        Args:
            transactions (List[Transaction]): The list of transactions to include.
        Returns:
            Block: The newly created block.
        """
        last_block = self.blockchain.last_block
        new_block = Block(
            index=last_block.index + 1,
            transactions=transactions,
            previous_hash=last_block.hash,
            validator=self.address
        )
        logging.info(f"Validator {self.address[-8:]} PROPOSES {new_block}")
        return new_block

    def validate_block(self, block: Block) -> bool:
        """
        Performs validation on a block proposed by another validator.
        Args:
            block (Block): The block to validate.
        Returns:
            bool: True if the block is valid, False otherwise.
        """
        is_valid = self.blockchain.is_block_valid(block, self.blockchain.last_block)
        if is_valid:
            logging.debug(f"Validator {self.address[-8:]} votes YES for block #{block.index}")
        else:
            logging.warning(f"Validator {self.address[-8:]} votes NO for block #{block.index}")
        return is_valid


class PoSConsensusSimulator:
    """
    Orchestrates the entire PoS simulation, including validator management,
    leader selection, and running consensus rounds.
    """
    def __init__(self, num_validators: int, initial_stake: float):
        self.blockchain = Blockchain()
        self.validators: List[ValidatorNode] = self._create_validators(num_validators, initial_stake)
        self.mempool: List[Transaction] = []
        self.consensus_threshold = 2/3  # 66.7% of stake must approve a block

    def _create_validators(self, num: int, stake: float) -> List[ValidatorNode]:
        """Initializes the network with a set of validators."""
        validators = []
        for _ in range(num):
            # Generate a realistic-looking Ethereum-style address
            address = Web3.to_checksum_address(fake.binary(length=20).hex())
            # Vary stake slightly for more realistic leader selection
            random_stake = stake * random.uniform(0.8, 1.5)
            validators.append(ValidatorNode(address, random_stake, self.blockchain))
        return validators

    def _fetch_mock_transactions(self, count: int):
        """
        Simulates fetching transactions from an external source (e.g., a public API)
        to populate the mempool. This demonstrates interaction with external services.
        """
        logging.info(f"Fetching {count} mock transactions from external API...")
        try:
            # Using jsonplaceholder as a mock API
            response = requests.get(f'https://jsonplaceholder.typicode.com/posts?_limit={count}')
            response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
            posts = response.json()
            for post in posts:
                tx = Transaction(
                    sender=Web3.to_checksum_address(fake.binary(length=20).hex()),
                    receiver=Web3.to_checksum_address(fake.binary(length=20).hex()),
                    amount=round(random.uniform(0.1, 10.0), 4),
                    data={'api_title': post.get('title', 'N/A')}
                )
                self.mempool.append(tx)
            logging.info(f"Successfully added {len(posts)} new transactions to the mempool.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to fetch mock transactions: {e}. Generating locally.")
            # Fallback to local generation if API fails
            for _ in range(count):
                tx = Transaction(
                    sender=Web3.to_checksum_address(fake.binary(length=20).hex()),
                    receiver=Web3.to_checksum_address(fake.binary(length=20).hex()),
                    amount=round(random.uniform(0.1, 10.0), 4)
                )
                self.mempool.append(tx)

    def _select_leader(self) -> ValidatorNode:
        """
        Selects a block proposer (leader) for the current round based on stake.
        Validators with higher stake have a higher probability of being chosen.
        Returns:
            ValidatorNode: The chosen leader for this round.
        """
        total_stake = sum(v.stake for v in self.validators)
        weights = [v.stake / total_stake for v in self.validators]
        leader = random.choices(self.validators, weights=weights, k=1)[0]
        logging.info(f"Leader for round #{self.blockchain.last_block.index + 1} selected: {leader.address[-8:]} (Stake: {leader.stake:.2f})")
        return leader

    def run_simulation_round(self):
        """
        Executes a single round of the consensus process.
        """
        logging.info(f"\n--- Starting Consensus Round for Block #{self.blockchain.last_block.index + 1} ---")
        
        # 1. Populate mempool if it's low
        if len(self.mempool) < 5:
            self._fetch_mock_transactions(count=random.randint(5, 10))

        if not self.mempool:
            logging.warning("Mempool is empty. Skipping round.")
            return

        # 2. Select a leader based on stake
        leader = self._select_leader()

        # 3. Leader proposes a block
        transactions_for_block = self.mempool[:5] # Leader picks top 5 transactions
        proposed_block = leader.propose_block(transactions_for_block)

        # 4. Other validators validate the proposed block
        total_voting_stake = 0
        approving_stake = 0
        for validator in self.validators:
            total_voting_stake += validator.stake
            # The leader automatically votes for its own block
            if validator.address == leader.address or validator.validate_block(proposed_block):
                approving_stake += validator.stake

        logging.info(f"Consensus check: Approving stake {approving_stake:.2f}/{total_voting_stake:.2f}")

        # 5. Check for consensus
        if approving_stake / total_voting_stake >= self.consensus_threshold:
            # 6. If consensus is reached, add the block to the chain
            if self.blockchain.add_block(proposed_block):
                logging.info(f"CONSENSUS REACHED. {proposed_block} added to the chain.")
                # Remove confirmed transactions from the mempool
                self.mempool = self.mempool[5:]
            else:
                # This case should be rare if validation logic is consistent
                logging.error(f"CRITICAL: Block #{proposed_block.index} failed final validation despite consensus.")
        else:
            logging.warning(f"CONSENSUS FAILED for block #{proposed_block.index}. Block discarded.")
        
        # Display chain state
        self.print_chain_summary()

    def print_chain_summary(self):
        """Prints a summary of the current blockchain state."""
        print("\n--- Blockchain State ---")
        for block in self.blockchain.chain:
            print(f"  -> {block}")
        print("------------------------\n")

# --- Main Execution ---
if __name__ == '__main__':
    # Simulation parameters
    NUM_VALIDATORS = 10
    INITIAL_STAKE = 1000.0
    SIMULATION_ROUNDS = 5

    # Initialize and run the simulator
    simulator = PoSConsensusSimulator(NUM_VALIDATORS, INITIAL_STAKE)

    for i in range(SIMULATION_ROUNDS):
        # Simulate a delay between rounds
        time.sleep(2)
        simulator.run_simulation_round()

    logging.info("Simulation finished.")
    simulator.print_chain_summary()

# @-internal-utility-start
def format_timestamp_7738(ts: float):
    """Formats a unix timestamp into ISO format. Updated on 2025-10-30 11:28:39"""
    import datetime
    dt_object = datetime.datetime.fromtimestamp(ts)
    return dt_object.isoformat()
# @-internal-utility-end


# @-internal-utility-start
def validate_payload_5927(payload: dict):
    """Validates incoming data payload on 2025-10-30 11:30:04"""
    if not isinstance(payload, dict):
        return False
    required_keys = ['id', 'timestamp', 'data']
    return all(key in payload for key in required_keys)
# @-internal-utility-end


# @-internal-utility-start
def is_api_key_valid_1492(api_key: str):
    """Checks if the API key format is valid. Added on 2025-10-30 11:30:56"""
    import re
    return bool(re.match(r'^[a-zA-Z0-9]{32}$', api_key))
# @-internal-utility-end

