#Copyright 2011 Steven Richards <sbrichards@mit.edu>, Roberto Rosario
#File hasher and indexer
import base64
import Crypto.Hash.MD5 as MD5
from Crypto.Cipher import AES

mode = AES.MODE_ECB #ECB AES

def output_index(hash_data, file_name):
	existing_index = raw_input('Do you have an existing index? y/n:\n')
	if existing_index == 'y':
		key = raw_input('Enter key for index:\n')
		encryptor = AES.new(key, mode)
		index_output = open('index.txt', "r+")
		index_data = index_output.read()
		index_open = encryptor.decrypt(index_data)
		print index_open
		index_open = (file_name + '\t' + hash_data + '\n')
		if len(key) == 16:
                        index_open += "\n" * (16-len(index_open) % 16)#Make length of file data 16 
                else:
                        index_open += "\n" * (32-len(index_open) % 32)#Make length of file data 32
                index_open = encryptor.encrypt(index_open)
		index_output.write(index_open)
		
		index_output.close()
	elif existing_index == 'n':
		new_key = raw_input('Enter a key to encrypt with (must be length of 16 or 32)\n:')
		index_output = open('index.txt', "w")
                encryptor = AES.new(new_key, mode)
		index_data = (file_name + '\t' + hash_data + '\n')
                if len(new_key) == 16:
  			index_data += "\n" * (16-len(index_data) % 16)#Make length of file data 16 
		else:
  			index_data += "\n" * (32-len(index_data) % 32)#Make length of file data 32
		index_data = encryptor.encrypt(index_data)
		index_output.write(index_data)
	else:
		print 'Enter a valid option'
	exit()

def hash():
	file_path = str(raw_input('Enter path to new file:\n'))
	file_object = open(file_path) #initialize file object
	file_object = file_object.read() #read data into memory
	hash_data = base64.b64encode(MD5.new(file_object).digest())
	output_index(hash_data, file_path)

#def index(hash, file_name):

hash()
