import hashlib
import json
import time
import os

CHAIN_PATH = os.path.join(os.path.dirname(__file__), 'chain.json')

class Block:
    def __init__(self, index: int, device_id: str, behavior_hash: str, previous_hash: str):
        self.index = index
        self.timestamp = time.time()
        self.device_id = device_id
        self.behavior_hash = behavior_hash
        self.previous_hash = previous_hash
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        block_str = json.dumps({
            'index': self.index,
            'timestamp': self.timestamp,
            'device_id': self.device_id,
            'behavior_hash': self.behavior_hash,
            'previous_hash': self.previous_hash
        }, sort_keys=True)
        return hashlib.sha256(block_str.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'device_id': self.device_id,
            'behavior_hash': self.behavior_hash,
            'previous_hash': self.previous_hash,
            'hash': self.hash
        }

class Blockchain:
    def __init__(self):
        self.chain: list[Block] = []
        self._load()
        if not self.chain:
            self._create_genesis()

    def _create_genesis(self):
        genesis = Block(0, 'GENESIS', 'GENESIS', '0')
        self.chain.append(genesis)
        self._save()

    def add_device(self, device_id: str, feature_vector: list) -> Block:
        behavior_hash = hashlib.sha256(
            json.dumps(feature_vector, sort_keys=True).encode()
        ).hexdigest()

        block = Block(
            index=len(self.chain),
            device_id=device_id,
            behavior_hash=behavior_hash,
            previous_hash=self.chain[-1].hash
        )
        self.chain.append(block)
        self._save()
        print(f"🔗 Block #{block.index} added | Device: {device_id} | Hash: {block.hash[:12]}...")
        return block

    def get_device(self, device_id: str) -> Block | None:
        for block in self.chain:
            if block.device_id == device_id:
                return block
        return None

    def verify_chain(self) -> bool:
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            if current.previous_hash != previous.hash:
                print(f"⚠️  Chain tampered at block {i}!")
                return False
            if current.hash != current.compute_hash():
                print(f"⚠️  Block {i} hash mismatch!")
                return False
        print("✅ Blockchain integrity verified.")
        return True

    def _save(self):
        with open(CHAIN_PATH, 'w') as f:
            json.dump([b.to_dict() for b in self.chain], f, indent=2)

    def _load(self):
        if not os.path.exists(CHAIN_PATH):
            return
        with open(CHAIN_PATH, 'r') as f:
            data = json.load(f)
        for d in data:
            b = Block.__new__(Block)
            b.__dict__.update(d)
            self.chain.append(b)

    def print_chain(self):
        print("\n📦 Blockchain State:")
        for b in self.chain:
            print(f"  Block #{b.index} | Device: {b.device_id:<20} | Hash: {b.hash[:16]}...")

if __name__ == '__main__':
    bc = Blockchain()
    bc.add_device('AA:BB:CC:DD:EE:01', [-45.2, 2.1, -50, -40, 21, 0.5, 3.0, 5, 500])
    bc.add_device('AA:BB:CC:DD:EE:02', [-70.5, 1.3, -75, -65, 10, 0.0, 1.0, 3, 200])
    bc.verify_chain()
    bc.print_chain()