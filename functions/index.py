#Copyright 2011 Steven Richards <sbrichards@mit.edu>, Roberto Rosario
#File hasher and indexer

import Crypto.Hash.MD5 as MD5
import base64

def output_index(hash_data, file_name):
	new_index = raw_input('Do you have an existing index? y/n:\n')
	if new_index == 'y':
		index_output = open('index.txt', "r+") #will add key verification
		index_data = index_output.read()
		index_data = file_name + '\t' + hash_data + '\n'
		index_output.write(index_data)
		index_output.close()
	elif new_index == 'n':
		index_output = open('index.txt', "w") #will add key $
                index_data = file_name + '\t' + hash_data + '\n'
                index_output.write(index_data)
                index_output.close() 
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
