from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
import Crypto.Random
import binascii

class Wallet:
	def __init__(self, node_id):
		self.private_key = None
		self.public_key = None
		self.node_id = node_id 

	def create_keys(self):
		private_key , public_key = self.generate_keys()
		self.private_key = private_key
		self.public_key = public_key

		
	def save_keys(self):
		try:
			with open("WalletKeys_%i.txt"%self.node_id, mode = "w") as f:
				f.write(self.private_key)
				f.write("\n")
				f.write(self.public_key)
			return True
		except:
			print("Saving keys FAILED.")
			return False


	def load_keys(self):
		try:
			with open("WalletKeys_%i.txt"%self.node_id, mode = "r") as f:
				loaded = f.readlines()
				self.private_key = loaded[0][:-1]
				self.public_key = loaded[1]
			return True

		except:
			print("Loading keys FAILED.")
			return False

	def generate_keys(self):
		private_key = RSA.generate(1024, Crypto.Random.new().read)
		public_key = private_key.publickey()
		return (binascii.hexlify(private_key.exportKey(format = "DER")).decode("ascii"), binascii.hexlify(public_key.exportKey(format = "DER")).decode("ascii"))

	def sign_transaction(self, sender, recipient, amount):
		signer = PKCS1_v1_5.new(RSA.importKey(binascii.unhexlify(self.private_key)))
		h = SHA256.new((str(sender) + str(recipient) + str(amount)).encode("utf8"))
		signature = signer.sign(h)
		return binascii.hexlify(signature).decode("ascii")

	@staticmethod
	def verify_transaction(transaction):
		if transaction.sender == "MINING":
			return True
		public_key = RSA.importKey(binascii.unhexlify(transaction.sender))
		verifier = PKCS1_v1_5.new(public_key)
		h = SHA256.new((str(transaction.sender) + str(transaction.recipient) + str(transaction.amount)).encode("utf8"))
		return verifier.verify(h, binascii.unhexlify(transaction.signature))







if __name__ == '__main__':
	w = Wallet()
	print(w.private_key)
	print("\n")
	print(w.public_key)