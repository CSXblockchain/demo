from flask import Flask , jsonify, request
from flask_cors import CORS 
import json

from wallet import Wallet 
from blockchain import BlockChain

app = Flask(__name__)
CORS(app)


#print(blockchain.get_chain())


@app.route("/", methods = ["GET"])
def get_ui():
	return "This works"

@app.route("/wallet", methods = ["POST"])
def create_wallet():
	wallet.create_keys()
	if wallet.save_keys():
		global blockchain
		blockchain = BlockChain(wallet.public_key, port)
		# By default will load previous blockchain data
		# May be set to adjustable on UI
		blockchain.load_data()
		response = {
		"public_key" : wallet.public_key,
		"private_key" : wallet.private_key,
		"Balance : " : blockchain.get_balance(wallet.public_key)
		}
		return jsonify(response), 201
	else:
		response = {
		"message" : "Saving keys failed."
		}
		return jsonify(response), 500
	
@app.route("/broadcast_block", methods = ["POST"])
def broadcast_block():
	values = request.get_json()
	if not values:
		response = {
		"message : " : "Data not found."
		}
		return jsonify(response), 400
	#required_fields = ["previous_hash", "index", "transactions", "proof", "time_stamp"]
	#if not all(field in values for field in required_fields):
	if  "block" not in values: 
		response = {
		"message : " : " Block data format is incorrect."
		}
		return response, 400
	# block_previous_hash = values["previous_hash"]
	# block_index = values["index"]
	# block_transactions = values["transactions"]
	# block_proof = values["proof"]
	# block_time_stamp = values["time_stamp"]
	block = values["block"]
	if block["index"] == blockchain.get_chain()[-1].index + 1:
		# block now is a dict
		# will be parsed in the add_block method
		success = blockchain.add_block(block)
		if not success:
			response = {
			"message" : "Block not added"
			}
			return jsonify(response), 409
		response = {
		"message" : "Block added successfully."
		}
		return jsonify(response), 201

	elif block["index"] > blockchain.get_chain()[-1].index + 1:
		response = {
		"message : " : "Blockchain seems to differ from local blockahain."
		}
		blockchain.resolve_conflicts = True
		return jsonify(response), 200
	else:
		response = {
		"message : " : "Blockchain seems to be shorter. Block not added."
		}
		return jsonify(response), 409





@app.route("/broadcast_transaction", methods = ["POST"])
def broadcast_transactions():
	values = request.get_json()
	if not values:
		response = {
		"message" : "No data found."
		}
		return jsonify(response), 400
	required_fields = ["sender", "recipient", "amount", "signature"]
	if not all(field in values for field in required_fields):
		response = {
		"message" : "Transaction data format is incorrect."
		}
		return jsonify(response), 400
	tx_sender, tx_recipient, tx_amount, tx_signature = values["sender"], values["recipient"], values["amount"], values["signature"]
	success = blockchain.add_transaction(tx_sender, tx_recipient, tx_sender, tx_signature,tx_amount, is_receiving = True )
	if success:
		response = {
		"Message : " : "Transaction successfully added.",
		"Transaction" :{ "sender" : tx_sender, "recipient" : tx_recipient, "amount" : tx_amount, "signature" : tx_signature},
		}
		return jsonify(response), 201
	else:
		response = {
		"Message : " : "Transaction failed. (Broadcasting)",
		}
		return jsonify(response), 500






@app.route("/transactions", methods = ["GET"])
def open_transactions():
	open_trans = blockchain.get_open_transactions()
	open_trans = [tx.to_ordered_dict() for tx in open_trans]
	response = {
	"message : " : "Current open transactions...",
	"Open transactions :" : open_trans
	}
	return jsonify(response), 200


@app.route("/transaction", methods = ["POST"])
def add_transaction():
	if wallet.public_key == None:
		response = {
		"Message : " : "Wallet not set up or created." 
		}
		return jsonify(response), 400

	values = request.get_json()
	if not values:
		response = {
		"Message : " : "No data found."
		}
		return jsonify(response), 400

	required_fields = ["recipient", "amount"]

	if not all(field in values for field in required_fields):
		response = {
		"Message : " : "Data format is not correct. "
		}
		return jsonify(response), 400

	tx_sender, tx_recipient, tx_amount = wallet.public_key, values["recipient"], values["amount"]

	signature = wallet.sign_transaction(tx_sender, tx_recipient, tx_amount)

	if blockchain.add_transaction(tx_sender, tx_recipient, wallet.public_key, signature, tx_amount):
		response = {
		"Message : " : "Transaction successfully added.",
		"Transaction" :{ "sender" : tx_sender, "recipient" : tx_recipient, "amount" : tx_amount},
		"Balance : " : blockchain.get_balance(wallet.public_key)
		}
		return jsonify(response), 201
	else:
		response = {
		"Message : " : "Transaction failed.",
		"Balance : " : blockchain.get_balance(wallet.public_key)
		}
		return jsonify(response), 500
		
	


@app.route("/wallet", methods = ["GET"])
def load_wallet():
	if wallet.load_keys():
		global blockchain
		blockchain = BlockChain(wallet.public_key, port)
		blockchain.load_data()
		response = {
		"public_key" : wallet.public_key,
		"private_key" : wallet.private_key,
		"Balance : " : blockchain.get_balance(wallet.public_key)
		}
		return jsonify(response), 201
	else:
		response = {
		"message" : "Loading keys failed."
		}
		return jsonify(response), 500

	
@app.route("/balance", methods = ["GET"])
def get_balance():
	current_balance = blockchain.get_balance(wallet.public_key)
	if not current_balance == False:
		response = {
		"message" : "Showing current balance...",
		"Wallet address : " : wallet.public_key,
		"Funds : " : current_balance
		}
		return jsonify(response), 200
	else:
		response = {
		"message" : "Showing current balance failed.",
		"Wallet set up": wallet.public_key != None,
		}
		return jsonify(response), 500

@app.route("/mine", methods = ["POST"])
def mine():
	if blockchain.resolve_conflicts:
		response = {
		"message : " : "Resolve conflicts first. Block not added"
		}
		return jsonify(response), 409
		
	if blockchain.mine_block():
		new_block = blockchain.get_chain()[-1].__dict__.copy()
		new_block["transactions"] = [tx.to_ordered_dict() for tx in new_block["transactions"]]
		response = {
		"message :" : "Adding a block successfully.",
		"Block : " : new_block,
		"balance : " : blockchain.get_balance(wallet.public_key)
		}
		return jsonify(response), 201
	else:
		response = {
		"message" : "Adding a block failed.",
		"Wallet set up" : wallet.public_key != None,

		}
		return jsonify(response), 500


@app.route("/resolve_conflicts", methods = ["POST"])
def resolve_conflicts():
	whether_replaced = blockchain.resolve()
	if whether_replaced:
		response = {
		"message : " : "Local blockchain replaced by peer chain." 
		}
	else:
		response = {
		"message : " : "Local chain not replaced."
		}
	return jsonify(response), 200

@app.route("/chain", methods = ["GET"])
def get_chain():
	chain_snapshot = blockchain.get_chain()
	dict_chain = [block.__dict__.copy() for block in chain_snapshot]
	for elem in dict_chain:
		elem["transactions"] = [tx.to_ordered_dict() for tx in elem["transactions"]]
	chain_json = jsonify(dict_chain)
	return chain_json, 200


@app.route("/node", methods = ["POST"])
def add_node():
	values = request.get_json()
	if not values:
		response = {
		"message " : "No data found."
		}
		return jsonify(response), 400
	if not "node" in values:
		response = {
		"message" : "No node URL found."
		}
		return jsonify(response), 400

	node_url = values["node"]
	blockchain.add_peer_node(node_url)
	response = {
	"message : " : "Node added.",
	"all_nodes : " : blockchain.show_peer_nodes()
	}
	return jsonify(response), 201
	

	



@app.route("/node/<node_url>", methods = ["DELETE"])
def remove_node(node_url):
	if node_url == "" or node_url == None:
		response = {
		"message : " : "No node url found." 
		}
		return jsonify(response), 400

	blockchain.remove_peer_node(node_url)
	response = {
	"message : " : "Node removed.",
	"all_nodes : " : blockchain.show_peer_nodes()
	}
	return jsonify(response), 200


@app.route("/node", methods = ["GET"])
def get_nodes():
	all_nodes = blockchain.show_peer_nodes()
	response = {
	"message : " : "Showing all nodes.",
	"all_nodes : " : all_nodes
	}
	return jsonify(response), 200




if __name__ == '__main__':
	from argparse import ArgumentParser
	parser = ArgumentParser()
	parser.add_argument("-p", "--port", type = int, default = 5000)
	args = parser.parse_args()
	port = args.port
	wallet = Wallet(port)
	blockchain = BlockChain(wallet.public_key,port)
	blockchain.load_data()
	app.run(host = "127.0.0.1", port = port)


