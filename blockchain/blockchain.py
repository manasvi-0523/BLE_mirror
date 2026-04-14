import hashlib
import time
import json

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
        # We hash the device ID and its behavior. This creates a tamper-proof signature.
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "device_id": self.device_id,
            "behavior_data": self.behavior_data,
            "previous_hash": self.previous_hash
        }, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

class SimpleBlockchain:
    def __init__(self):
        self.chain = [self.create_genesis_block()]

    def create_genesis_block(self):
        # The genesis block kicks off the local chain
        return Block(0, time.time(), "Genesis", {"status": "Genesis Block"}, "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_block(self, device_id, behavior_data):
        """Adds a verified device and its behavior into the immutable ledger"""
        previous_block = self.get_latest_block()
        new_block = Block(
            index=previous_block.index + 1,
            timestamp=time.time(), # Cryptographic timestamp
            device_id=device_id,
            behavior_data=behavior_data,
            previous_hash=previous_block.hash
        )
        self.chain.append(new_block)
        print(f"[Blockchain] Block {new_block.index} Mined: Device {device_id} secured.")
        return new_block
        
    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i-1]
            
            # Recalculate hash to ensure no tampering
            if current.hash != current.calculate_hash():
                return False
                
            # Verify chain link
            if current.previous_hash != previous.hash:
                return False
        return True

    def get_device_history(self, device_id):
        # Returns all blocks associated with a specific MAC Address
        history = [block for block in self.chain if block.device_id == device_id]
        return history

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
    
    print("\n--- Immutable Ledger Snapshot ---")
    for block in trust_registry.chain:
        print(f"Block {block.index} | Device: {block.device_id:17} | Hash: {block.hash[:20]}...")
