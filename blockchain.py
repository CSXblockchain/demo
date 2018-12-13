import json
import requests

from utility.printable import Printable
from utility.verification import Verification
from utility.hash_util import hash_block, hash_string_256
from block import Block
from transaction import Transaction
from wallet import Wallet


MINING_REWARD = 10 #GLOBAL VARIABLE

# hosting_node = public_key

class BlockChain:
	def __init__(self, hosting_node, node_id):
		self.genesis_block = Block(0,"",[],100,0)
		self.__chain = [self.genesis_block]
		self.__open_transactions = []
		self.hosting_node = hosting_node
		self.participants = {self.hosting_node}
		self.resolve_conflicts = False
		self.node_id = node_id 
		self.__peer_nodes = set()
		#self.load_data()

	def get_chain(self):
		return self.__chain[:]


	def get_open_transactions(self):
		return self.__open_transactions[:]


	def proof_of_work(self):
		last_block = self.__chain[-1]
		last_hash = hash_block(last_block)
		proof = 0
		while not Verification.valid_proof(self.__open_transactions, last_hash, proof):
			proof = proof + 1
		return proof 


	def get_balance(self,participant):
		try:
			tx_sender = [[tx.amount for tx in block.transactions if tx.sender == participant] for block in self.__chain]
			open_tx_sender = [tran.amount for tran in self.__open_transactions if tran.sender == participant]
			tx_recipient = [[tx.amount for tx in block.transactions if tx.recipient == participant] for block in self.__chain]
			total_send = sum([sum(x) for x in tx_sender if len(x) > 0])
			total_tx_send = sum(open_tx_sender)
			total_receive = sum([sum(x) for x in tx_recipient if len(x) > 0])
			return total_receive - total_send - total_tx_send
		except:
			return False

	def get_last_blockchain_value(self):
		if len(self.__chain) == 0:
			return None
		return self.__chain[-1]

	def add_transaction(self, sender, recipient, public_key, signature, amount = 1.0, is_receiving = False):
		# transaction = {
		# "sender" : sender, 
		# "recipient": recipient, 
		# "amount": amount}

		transaction = Transaction(sender, recipient, signature, amount)
		if not Wallet.verify_transaction(transaction):
			print("Invalid signature.")
			return False
		if Verification.verify_transaction(transaction, self.get_balance):
			self.__open_transactions.append(transaction)
			self.participants.add(sender)
			self.participants.add(recipient)
			self.save_data()
			if not is_receiving:
				# Broadcasting the new open transaction to other peer nodes
				for node in self.__peer_nodes:
					url = "http://{}/broadcast_transaction".format(node)
					try:
						response = requests.post(url, json = {"sender": sender, "recipient" : recipient, "amount" : amount, "signature" : signature})
						if response.status_code == 400 or response.status_code == 500:
							print("Transaction declined. ")
							return False
					except requests.exceptions.ConnectionError:
						print("Connection failed with node : %s"%node)
						continue
			return True
		return False

# After mining a new block, the new block should be broadcasted to other peer_nodes

	def mine_block(self):
		if self.hosting_node == None:
			return False 
		last_block = self.__chain[-1]
		hashed_block = hash_block(last_block)
		#print(hashed_block)
		print("Mining new block...")
		proof = self.proof_of_work()
		mining_transaction =  Transaction("MINING", self.hosting_node, "", MINING_REWARD)
		copied_open_transactions = self.__open_transactions[:]
		copied_open_transactions.append(mining_transaction)
		block = Block(len(self.__chain), hashed_block, copied_open_transactions, proof)

		for tx in block.transactions:
			if not Wallet.verify_transaction(tx):
				print("Invalid signature found during mining.")
				return False
		self.__chain.append(block)
		self.__open_transactions = []
		self.save_data()
		# Broadcasting the new block
		# First convert the Block Object into a dict
		# then convert the transaction objects into list of objects
		dict_block_for_broadcasting = block.__dict__.copy()
		dict_block_for_broadcasting["transactions"] = [tx.__dict__ for tx in dict_block_for_broadcasting["transactions"]]
		for node in self.__peer_nodes:
			url = "http://{}/broadcast_block".format(node)
			try:
				response = requests.post(url, json = {"block": dict_block_for_broadcasting})
				if response.status_code == 400 or response.status_code == 500:
					print(response.json())
					print("Block broadcasting declined.")
					#return False
				if response.status_code == 409:
					self.resolve_conflicts = True
					print("Conflicts found!!")
			except requests.exceptions.ConnectionError:
				print("Connection failed with node : %s"%node)
				continue
		return True


	def add_block(self, block):
		# Receiving broadcasting block
		# input block format is in DICT
		# valid_proof should be avoid MINING REWARD
		transactions_to_valid_proof = [Transaction(tx["sender"],tx["recipient"],tx["signature"],tx["amount"]) for tx in block["transactions"][:-1]]
		transactions_to_final_add = [Transaction(tx["sender"],tx["recipient"],tx["signature"],tx["amount"]) for tx in block["transactions"]]
		proof_is_valid = Verification.valid_proof(transactions_to_valid_proof , block["previous_hash"], block["proof"])
		hashes_match = hash_block(self.get_chain()[-1]) == block["previous_hash"]
		print(proof_is_valid)
		print(hashes_match)
		if proof_is_valid and hashes_match:
			self.__chain.append(Block(block["index"],block["previous_hash"],transactions_to_final_add,block["proof"],block["time_stamp"]))
			# Clean the Open_transactions
			# ISSUE: SAME SENDER & SAME RECIPIENT & SAME AMOUNT & SAME SIGNATURE
			# still need to solve!!
			stored_local_open_trans = self.__open_transactions[:]
			for in_trans in block["transactions"]:
				for op_tx in stored_local_open_trans:
					if in_trans["sender"] == op_tx.sender and in_trans["recipient"] == op_tx.recipient and in_trans["amount"] == op_tx.amount and in_trans["signature"] == op_tx.signature:
						try:
							self.__open_transactions.remove(op_tx)
						except ValueError:
							print("Transaction already removed.")
			self.save_data()
			return True
		else:
			return False


	def resolve(self):
		winner_chain = self.get_chain()
		whether_replace_local_chain = False
		for node in self.__peer_nodes:
			url = "http://{}/chain".format(node)
			try:
				response = requests.get(url)
				peer_chain = response.json()
				peer_chain = [Block(block["index"], block["previous_hash"], block["transactions"], block["proof"], block["time_stamp"]) for block in peer_chain]
				for elem in peer_chain:
					elem.transactions = [Transaction(tx["sender"], tx["recipient"], tx["signature"], tx["amount"]) for tx in elem.transactions]
				peer_chain_length = len(peer_chain)
				local_chain_length = len(winner_chain)
				whether_peer_chain_longer = peer_chain_length > local_chain_length
				whether_peer_chain_valid = Verification.verify_chain(peer_chain)
				if whether_peer_chain_longer and whether_peer_chain_valid:
					winner_chain = peer_chain[:]
					whether_replace_local_chain = True 

			except requests.exceptions.ConnectionError:
				print("Connection failed with node : %s"%node)
				continue
		self.resolve_conflicts = False 
		self.__chain = winner_chain
		if whether_replace_local_chain:
			self.__open_transactions = []
		self.save_data()
		return whether_replace_local_chain





	# Should add the function that the user can INPUT the file name that want to load the blockchain data
	def load_data(self):
		try:
			with open("basicBlockChain%i.txt"%self.node_id, mode = "r") as f:
				loaded = f.readlines()
				loaded_blockchain = loaded[0][:-1]
				#print(loaded_blockchain)
				loaded_open_transactions = loaded[1][:-1]
				loaded_peer_nodes = loaded[2]
				#print(loaded_open_transactions)
				blockchain = json.loads(loaded_blockchain)
				updated_blockchain = []
				for block in blockchain:
					converted_tx = []
					for tx in block["transactions"]:
						tx_obj = Transaction(tx["sender"], tx["recipient"], tx["signature"], tx["amount"])
						converted_tx.append(tx_obj)
					updated_block = Block(block["index"], block["previous_hash"], converted_tx, block["proof"], block["time_stamp"])
					updated_blockchain.append(updated_block)
				self.__chain = updated_blockchain
				
				open_transactions = json.loads(loaded_open_transactions)
				updated_open_transactions = []
				for tx in open_transactions:
					open_tx_obj = Transaction(tx["sender"], tx["recipient"], tx["signature"], tx["amount"])
					updated_open_transactions.append(open_tx_obj)
				self.__open_transactions = updated_open_transactions
				peer_nodes = json.loads(loaded_peer_nodes)
				self.__peer_nodes = set(peer_nodes)

			# Update participants
			for block in self.__chain:
				for tx in block.transactions:
					self.participants.add(tx.sender)
					self.participants.add(tx.recipient)
			for tx in self.__open_transactions:
				self.participants.add(tx.sender)
				self.participants.add(tx.recipient)

		except IOError:
			print("IO Error. File not found.")

		except IndexError:
			print("IndexError. File is empty.")

	# Should add the function that user can INPUT the file name that want to save the blockchain data
	def save_data(self):
		try:
			with open("basicBlockChain%i.txt"%self.node_id, mode = "w") as f:
				saveable_blockchain = [block.__dict__.copy() for block in self.__chain]
				for block in saveable_blockchain:
					block["transactions"] = [tx.to_ordered_dict() for tx in block["transactions"]]
				f.write(json.dumps(saveable_blockchain))
				f.write("\n")
				saveable_open_transactions = [tx.to_ordered_dict() for tx in self.__open_transactions]
				f.write(json.dumps(saveable_open_transactions))
				f.write("\n")
				f.write(json.dumps(list(self.__peer_nodes)))
		except:
			print("Saving file failed.")


	def add_peer_node(self,node):
		# Node should be an URL
		self.__peer_nodes.add(node)
		self.save_data()

	def remove_peer_node(self,node):
		# Node should be an URL
		self.__peer_nodes.discard(node)
		self.save_data()

	def show_peer_nodes(self):
		return list(self.__peer_nodes.copy())

