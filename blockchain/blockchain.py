import hashlib
import time
import json
import os
import sys

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import CHAIN_PATH

class Block:
    def __init__(self, index, timestamp, device_id, behavior_data, previous_hash):
        self.index = index
        self.timestamp = timestamp
        self.device_id = device_id
        # We store the exact mathematical blueprint of normal behavior
        self.behavior_data = behavior_data 
        self.previous_hash = previous_hash
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        """
        Calculate SHA-256 hash of the block.
        This creates a tamper-proof signature.
        """
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "device_id": self.device_id,
            "behavior_data": self.behavior_data,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def to_dict(self):
        """Convert block to dictionary for JSON serialization."""
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "device_id": self.device_id,
            "behavior_data": self.behavior_data,
            "previous_hash": self.previous_hash,
            "hash": self.hash
        }
    
    @staticmethod
    def from_dict(data):
        """Create a Block instance from a dictionary."""
        block = Block.__new__(Block)
        block.index = data["index"]
        block.timestamp = data["timestamp"]
        block.device_id = data["device_id"]
        block.behavior_data = data["behavior_data"]
        block.previous_hash = data["previous_hash"]
        block.hash = data["hash"]
        return block

class SimpleBlockchain:
    def __init__(self, load_from_disk=True):
        """
        Initialize the blockchain.
        
        Args:
            load_from_disk: If True, attempt to load existing chain from disk
        """
        self.chain_path = str(CHAIN_PATH)
        os.makedirs(os.path.dirname(self.chain_path), exist_ok=True)
        
        if load_from_disk and os.path.exists(self.chain_path):
            self._load_chain()
        else:
            self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        """Create the first block in the chain."""
        return Block(0, time.time(), "Genesis", {"status": "Genesis Block"}, "0")

    def get_latest_block(self):
        """Get the most recent block in the chain."""
        return self.chain[-1]

    def add_block(self, device_id, behavior_data, force=False):
        """
        Adds a verified device and its behavior into the immutable ledger.
        
        Args:
            device_id: MAC address of the device
            behavior_data: Dict containing behavioral fingerprint
            force: If True, add block even if device already exists
            
        Returns:
            Block: The newly created block, or None if duplicate prevented
        """
        # Prevent duplicate entries unless forced
        if not force:
            existing = self.get_device_history(device_id)
            if existing:
                # Check if behavior has meaningfully changed
                last_behavior = existing[-1].behavior_data
                if self._behaviors_similar(last_behavior, behavior_data):
                    print(f"[Blockchain] Device {device_id} already in ledger with similar behavior. Skipping.")
                    return None
        
        previous_block = self.get_latest_block()
        new_block = Block(
            index=previous_block.index + 1,
            timestamp=time.time(),  # Cryptographic timestamp
            device_id=device_id,
            behavior_data=behavior_data,
            previous_hash=previous_block.hash
        )
        self.chain.append(new_block)
        print(f"[Blockchain] Block {new_block.index} Mined: Device {device_id} secured.")
        
        # Save to disk after adding
        self._save_chain()
        
        return new_block
    
    def _behaviors_similar(self, behavior1, behavior2, tolerance=0.1):
        """
        Compare two behavior dictionaries to see if they're similar.
        
        Args:
            behavior1: First behavior dict
            behavior2: Second behavior dict
            tolerance: Relative tolerance for numerical comparison (10% default)
            
        Returns:
            bool: True if behaviors are similar enough
        """
        # Compare numerical fields with tolerance
        numerical_keys = ['mean_rssi', 'mean_interval_ms', 'packet_count']
        for key in numerical_keys:
            if key in behavior1 and key in behavior2:
                val1 = behavior1[key]
                val2 = behavior2[key]
                if val1 == 0 and val2 == 0:
                    continue
                if val1 == 0 or val2 == 0:
                    if abs(val1 - val2) > 5:  # Absolute difference for zero cases
                        return False
                else:
                    rel_diff = abs(val1 - val2) / max(abs(val1), abs(val2))
                    if rel_diff > tolerance:
                        return False
        return True
        
    def is_chain_valid(self):
        """
        Verify the integrity of the blockchain.
        
        Returns:
            bool: True if chain is valid, False if tampered
        """
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            # Recalculate hash to ensure no tampering
            if current.hash != current.calculate_hash():
                print(f"[Blockchain] Block {i} has been tampered with!")
                return False
                
            # Verify chain link
            if current.previous_hash != previous.hash:
                print(f"[Blockchain] Chain broken at block {i}!")
                return False
        return True

    def get_device_history(self, device_id):
        """
        Returns all blocks associated with a specific MAC Address.
        
        Args:
            device_id: MAC address to search for
            
        Returns:
            list: List of Block objects for this device
        """
        history = [block for block in self.chain if block.device_id == device_id]
        return history
    
    def _save_chain(self):
        """Save the blockchain to disk."""
        try:
            chain_data = [block.to_dict() for block in self.chain]
            with open(self.chain_path, 'w') as f:
                json.dump(chain_data, f, indent=2)
        except Exception as e:
            print(f"[Blockchain] Warning: Failed to save chain: {e}")
    
    def _load_chain(self):
        """Load the blockchain from disk and verify integrity."""
        try:
            with open(self.chain_path, 'r') as f:
                chain_data = json.load(f)
            
            self.chain = [Block.from_dict(block_dict) for block_dict in chain_data]
            
            # Verify the loaded chain
            if self.is_chain_valid():
                print(f"[Blockchain] Loaded {len(self.chain)} blocks from disk. Chain integrity verified.")
            else:
                print("[Blockchain] Warning: Loaded chain failed integrity check. Starting fresh.")
                self.chain = [self.create_genesis_block()]
        except Exception as e:
            print(f"[Blockchain] Error loading chain: {e}. Starting fresh.")
            self.chain = [self.create_genesis_block()]

if __name__ == "__main__":
    print("--- Local Blockchain Trust Registry Simulation ---")
    trust_registry = SimpleBlockchain()
    
    # Simulate storing a baseline normal device behavior (from our AI outputs)
    sample_behavior = {
        "mean_rssi": -65.2,
        "mean_interval_ms": 105.4,
        "packet_count": 25,
        "services": 1
    }
    
    print("\nSaving new verified devices...")
    trust_registry.add_block(device_id="41:42:81:36:39:A6", behavior_data=sample_behavior)
    trust_registry.add_block(device_id="DD:1C:6D:8D:2E:D7", behavior_data={"status": "normal"})
    
    # Try adding duplicate
    trust_registry.add_block(device_id="41:42:81:36:39:A6", behavior_data=sample_behavior)
    
    print("\n--- Immutable Ledger Snapshot ---")
    for block in trust_registry.chain:
        print(f"Block {block.index} | Device: {block.device_id:17} | Hash: {block.hash[:20]}...")
    
    print(f"\n--- Chain Validity Check ---")
    print(f"Chain is valid: {trust_registry.is_chain_valid()}")
