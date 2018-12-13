from uuid import uuid4
from blockchain import BlockChain
from utility.verification import Verification
from wallet import Wallet


class Node:
	def __init__(self):
		self.wallet = Wallet()
		# By default the node generate a new wallet while the user
		# can still generate a new WALLET
		self.wallet.create_keys()
		self.blockchain = BlockChain(self.wallet.public_key)
		#self.blockchain = None
		
		
	def get_transaction_value(self):
		#tx_sender = input("Enter the sender of the transaction:")
		tx_sender = self.wallet.public_key
		tx_recipient = input("Enter the recipient of the transaction:")
		tx_amount = float(input("Enter the amount of the transaction:"))
		return tx_sender, tx_recipient, tx_amount

	def print_blockchain_elements(self):
		for block in self.blockchain.get_chain():
			print(block)
		else:
			print("-"*30)


	def get_user_choice(self):
		return int(input("Your choice:"))


	def display_balance_all(self):
		for person in self.blockchain.participants:
			print("Balance of {} : {:6.2f}".format(person,self.blockchain.get_balance(person)))

	def listen_for_input(self):
		waiting_for_input = True
		while waiting_for_input:
			print("Please select your choice: ")
			print("1) Add a a new transaction. ")
			print("2) Mine a new block")
			print("3) Print the blockchain. ")
			print("4) Show participants. ")
			print("5) Manipulate. ")
			print("6) Verify. ")
			print("7) Quit. ")
			print("8) Load Data.")
			print("9) Create Wallet")
			print("10) Load Wallet")
			print("11) Save Keys")
			user_choice = self.get_user_choice()
			if user_choice == 1:
				tx_sender, tx_recipient, tx_amount = self.get_transaction_value()
				signature = self.wallet.sign_transaction(tx_sender, tx_recipient, tx_amount)
				if self.blockchain.add_transaction(tx_sender, tx_recipient, self.wallet.public_key, signature, tx_amount):
					print("Transaction successfully added.")
				else:
					print("Transaction failed.")
				print([tx.__dict__ for tx in self.blockchain.get_open_transactions()])
			elif user_choice == 2:
				if self.blockchain.mine_block():
					print(" New Block Mined!")
			elif user_choice == 3:
				self.print_blockchain_elements()
			elif user_choice == 4:
				print(self.blockchain.participants)
			elif user_choice == 5:
				print("NONE")
			elif user_choice == 6:
				print(Verification.verify_chain(self.blockchain.get_chain()))

			elif user_choice == 7:
				waiting_for_input = False

			elif user_choice == 8:
				self.blockchain.load_data()

			elif user_choice == 9: # Create Wallet
				self.wallet.create_keys()
				self.blockchain = BlockChain(self.wallet.public_key)
				print(self.wallet.public_key)

			elif user_choice == 10: # Load Wallet
				self.wallet.load_keys()
				self.blockchain = BlockChain(self.wallet.public_key)
				print(self.wallet.public_key)

			elif user_choice == 11: # Save the keys
				if self.wallet.save_keys():
					print("Keys SAVED.")
				else:
					print("Keys NOT saved.")
				

			else:
				print("Not a valid input.")

			if not Verification.verify_chain(self.blockchain.get_chain()):
				print("Invalid blockchain")
				self.print_blockchain_elements()
				waiting_for_input = False

			self.display_balance_all()

			
		else:
			print("User left.")