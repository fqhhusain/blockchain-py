import hashlib
import datetime
import json
import time
import tracemalloc

class Transaction:
  def __init__(self, sender, receiver, amount):
    self.sender = sender
    self.receiver = receiver
    self.amount = amount
    
  def to_dict(self):
    return {
      "sender": self.sender,
      "receiver": self.receiver,
      "amount": self.amount
    }    
  
  def print(self):
    print(self.to_dict())


class Block:

    def __init__(self, index, transactions, previous_hash):
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.nonce = 0
        self.timestamp = str(datetime.datetime.now())
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block = {
            "index": self.index,
            "transactions": [t.to_dict() for t in self.transactions],
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
        }
        block_string = json.dumps(block, sort_keys=True)
        generated_hash = hashlib.sha256(block_string.encode()).hexdigest()
        return generated_hash

    def mine_block(self, difficulty):
        start = time.time()
        tracemalloc.start()

        while self.hash[:difficulty] != "0" * difficulty:
            self.nonce += 1
            self.hash = self.calculate_hash()
        print("Block mined:", self.hash)

        end = time.time()
        print("Waktu eksekusi:", end - start, "detik")
        
        current, peak = tracemalloc.get_traced_memory()
        print("Memory sekarang:", current / 10**6, "MB")
        print("Memory maksimum:", peak / 10**6, "MB")
        tracemalloc.stop()


class Blockchain:
    def __init__(self):
        self.chain = [self.init_genesis_block()]
        self.pending_transactions = []
        self.difficulty = 5

    def init_genesis_block(self):
        return Block(0, [], "0")

    def get_latest_block(self):
        return self.chain[-1]

    def add_transactions(self, transaction):
        self.pending_transactions.append(transaction)

    def mine_pending_transactions(self):
        index = len(self.chain)
        previous_hash = self.get_latest_block().hash
        block = Block(
            index, self.pending_transactions, previous_hash
        )
        block.mine_block(self.difficulty)
        self.chain.append(block)
        self.pending_transactions = []
        
    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            prev = self.chain[i-1]
            
            if current.hash != current.calculate_hash():
                return False
            
            if current.previous_hash != prev.hash:
                return False 
    
        return True


if __name__ == "__main__":
    my_blockchain = Blockchain()

    trans1 = Transaction("Alice", "Bob", 10)
    print("Transaksi 1")
    trans1.print()
    print("\n")

    trans2 = Transaction("Bob", "Charlie", 5)
    print("Transaksi 2")
    trans2.print()
    print("\n")

    my_blockchain.add_transactions(trans1)
    my_blockchain.add_transactions(trans2)

    print("Mining block...")
    my_blockchain.mine_pending_transactions()
    print("\n")

    trans3 = Transaction("Charlie", "Diana", 3)
    print("Transaksi 3")
    trans3.print()

    print("Mining block...")
    my_blockchain.mine_pending_transactions()
    print("\n")

    print("Blockchain valid?", my_blockchain.is_chain_valid())