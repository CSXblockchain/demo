# The Simplest BlockChain
# In Separate Modules

from old_node import Node

if __name__ == '__main__':
	local_node = Node()
	local_node.listen_for_input()
