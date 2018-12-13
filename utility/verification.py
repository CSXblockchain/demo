from utility.hash_util import hash_block, hash_string_256
from wallet import Wallet


class Verification:
	@classmethod
	def verify_chain(cls,blockchain):
		for ind, block in enumerate(blockchain):
			if ind == 0:
				continue
			else:
				if not block.previous_hash == hash_block(blockchain[ind - 1]):
					print("previous_hash invalid")
					return False
				if not cls.valid_proof(block.transactions[:-1],block.previous_hash,block.proof):
					print("POW invalid")
					return False
				for tx in block.transactions:
					if not Wallet.verify_transaction(tx):
						return False
		return True

	@staticmethod
	def verify_transaction(transaction,get_balance_func):
		if get_balance_func(transaction.sender) >= transaction.amount:
			return True
		return False

	@staticmethod
	def valid_proof(transactions, last_hash, proof):
		guess = (str([tx.to_ordered_dict() for tx in transactions]) + str(last_hash) + str(proof)).encode()
		guess_hash = hash_string_256(guess)
		#print(guess_hash)
		return guess_hash[0:5] == "00000"
	