import hashlib
import json
from time import time
from textwrap import dedent
from uuid import uuid4
from flask import Flask, jsonify, request
from urllib.parse import urlparse
import requests


class Blockchain(object):
    '''the constructor stores a blockchain and transactions.'''
    def __init__(self) -> None:
        self.chain = []
        self.current_trasactions = []
        self.nodes = set()

        # create a genesis block
        self.new_block(proof=100, previous_hash=1)

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
        self.current_trasactions.append({
            'sender':sender,
            'recipient':recipient,
            'amount':amount
        })
        
        return self.last_block['index']+1 

    def register_node(self, address):
        '''add new node to the list of nodes
        :param address: <str> address of the node eg, https://192.168.0.5:5000
        :return: None
        '''

        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)

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

    def valid_chain(self, chain):
        '''check if a given chain is valid
        by checking hash of of current block, and proof of current and last block
        :param chain: <list> A blockchain from a node
        :return: <bool> True if valid, else False
        '''
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            print(f"{last_block}")
            print(f"{block}")
            print("\n-------------\n")

            #check if hash of a block is correct 
            if block['previous_hash']!=self.hash(last_block):
                return False
            
            #check if proof of work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            
            last_block = block
            current_index = current_index+1
        
        return True
    
    def resolve_conflicts(self):
        '''Consensus algorith to resolve conflicts 
        by replacing the chain with longest chain in the network.
        :return: <bool> True if chain is replaced, False if not. 
        '''

        neighbours = self.nodes
        new_chain = None

        #look for chain longer than current node's
        max_length = len(self.chain)

        #retrieve and verify chains from all the nodes
        for node in neighbours:
            response = requests.get(f"http://{node}/chain")

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']

                #check current node chain length vs response node's
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        
        # replace current chain with new valid chain
        if new_chain:
            self.chain = new_chain
            return True

        return False
            

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

@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    
    if nodes is None:
        return "Error : Enter list of valid nodes", 400

    for node in nodes:
        blockchain.register_node(nodes)

    response = {
        'message':'New nodes have been registered',
        'total_nodes': list(blockchain.nodes)
    } 

    return jsonify(response), 201

@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()

    if replaced:
        response = {
            'message': 'Current nodes chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Chain is authoritative',
            'chain': blockchain.chain
        }

    return jsonify(response), 200


if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)


