import hashlib
import json
from time import time


class Blockchain(object):
    '''the constructor stores a blockchain and transactions.'''
    def __init__(self) -> None:
        self.chain = []
        self.current_trasactions = []


    def new_block(self, proof, previous_hash=None):
        '''creates new block and adds it to the chain
        :param proof: <int> proof given by proof of work algo
        :param previous_hash: optional type <str> hash of the previous block
        :returns: <dict> new block 
        '''
        block = {
            'index':len(self.chain)+1,
            'timestamp': time(),
            'transactions':self.current_trasactions,
            'proof':proof,
            'previous_hash':previous_hash or self.hash(self.chain[-1]) 
        }
    
        #once new block is created, reset current list of trax, for next/new block
        self.current_trasactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount):
        '''adds new trax to the list of traxs, until block limit
        this new transaction goes into the next mined block
        and returns index of the block that'll hold this trax.
        '''
        self.current_trasaction.append({
            'sender':sender,
            'recipient':recipient,
            'amount':amount
        })
        
        return self.last_block['index']+1 

    @staticmethod
    def hash(block):
        '''hashes a block with sha-256
        :param: <dict> Block
        :return: <str>
        dictionary has to be ordered or there'll be inconsistent hashes
        '''
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    @property
    def last_block(self):
        '''returns the last block in the chain'''
        return self.chain[-1]

