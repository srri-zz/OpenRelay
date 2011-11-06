#Copyright 2011 Steven Richards <sbrichards@mit.edu>, Roberto Rosario
#File encryption and decryption - GPG
import gnupg
from cStringIO import StringIO
gpg = gnupg.GPG()

def new_key():
	#key_input = { #Key Parameters
	#	'Key-Type': 'RSA',
	#	'Key-Length': 2048,
	#	'Passphrase': raw_input('\nEnter a passphrase: '),
	#	'Expire-data': 0,
	#	'Name-Real': raw_input('\nEnter your name: '),
	#	'Name-Email': raw_input('\nEnter your email: ')    
	#	    }
	key_params = gpg.gen_key_input(passphrase = raw_input('\nEnter a passphrase: ')) #Define input parameters
	key = gpg.gen_key(key_params) #Generate key
	print '\nGenerating key...\n'
	pub = gpg.export_keys(key.fingerprint)
	priv = gpg.export_keys(key.fingerprint, True)
	print pub + '\n' + priv 
	pub_out = open('pub-openrelay.gpg', 'w') #Output key
	priv_out = open('priv-openrelay.gpg', 'w')
	pub_out.write(pub)
	priv_out.write(priv)
	pub_out.close()
	priv_out.close()	
	print 'Your public key is pub-openrelay.gpg'
	print 'Your private key is priv-openrelay.gpg'

def encrypt():
	keys_file = str(raw_input('Enter path to key data:\n'))
	keys_open = open(keys_file, 'r+')
	key = gpg.import_keys(keys_open.read())
	print key.count
	file_unenc = open(str(raw_input('Enter path to file to be encrypted:\n')), 'r+')
	file_unenc_data = file_unenc.read()
        fingerprint = key.fingerprints
	file_enc = gpg.encrypt_file(StringIO(file_unenc_data), fingerprint,  output='encrypted.txt')
	#no error, but no encrypted.txt
	#Call indexing function somewhere here... Index/Hash the encrypted file and unencrypted file
# needs to be added def decrypt(key, other)

#Private key is not being generated...	
new_key()
encrypt()
