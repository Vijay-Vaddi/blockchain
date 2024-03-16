import hashlib
import json
from time import time
from textwrap import dedent
from uuid import uuid4
from flask import Flask, jsonify, request


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


    def proof_of_work(self, last_proof):
        '''find p such that hash(pp') has last 4 digits to be 0
        p is previous proof of work, p' is current
        :param last_proof:<int>
        :return:<int>'''

        proof = 0

        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof
    

    @staticmethod
    def valid_proof(last_proof, proof):
        '''validates the proof such that hash(p, p') concatenation of p, p'
        returns true if ....0000'''

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"

# instantiate app/node
app = Flask(__name__)

# generate a globally unique address for this code. (?)
node_identifier = str(uuid4()).replace('-','')

#instantiate blockchain
blockchain = Blockchain()

@app.route('/mine', methods=['GET'])
def mine():
    '''run PoW algorithm to get next proof'''
    last_block = blockchain.last_block
    last_proof= last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    '''receive reward for finding proof
    Sender is '0' to indicate this node has mined the new coin'''
    blockchain.new_transaction(
        sender='0',
        recipient=node_identifier,
        amount=1
    )

    # create new block by adding it to the chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    response = {
        'message':'New block forged',
        'index':block['index'],
        'transactions': block['transactions'],
        'proof':block['proof'],
        'previous_hash':block['previous_hash'],
    }
    return jsonify(response), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()

    #check if all values for trax exists in the POSTed data. 
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing parameters', 400
    
    #create a new trax
    index = blockchain.new_transaction(values['sender'], values['recipient'],
                                       values['amount'])
    response = {'message': f"Adding transaction to the block {index}"}
    return jsonify(response), 201


@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'lenght': len(blockchain.chain)
    }
    return jsonify(response), 200

if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


