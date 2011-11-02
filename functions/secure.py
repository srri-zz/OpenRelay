#Copyright 2011 Steven Richards <sbrichards@mit.edu>, Roberto Rosario
#File encryption and decryption - GPG
import gnupg

gpg = gnupg.GPG()

def new_key():
	key_input = { #Key Parameters
		'Key-Type': 'RSA',
		'Key-Length': 2048,
		'Passphrase': raw_input('\nEnter a key: '),
		'Expire-data': 0,
		'Name-Real': raw_input('\nEnter your name: '),
		'Name-Email': raw_input('\nEnter your email: ')    
		    }
	key = gpg.gen_key_input(**key_input) #Define input parameters
	key = gpg.gen_key(key) #Generate key
	print '\nGenerating key...\n'
	pub = gpg.export_keys(key)
	#priv = gpg.export_keys(key, True)
	#print pub + '\n' + priv 
	pub_out = open('pub-openrelay.gpg', 'w') #Output key
	#priv_out = open('priv-openrelay.gpg', 'w')
	pub_out.write(pub)
	#priv_out.write(priv)
	pub_out.close()
	#priv_out.close()	
	print 'Your public key is pub-openrelay.gpg'
	#print 'Your private key is priv-openrelay.gpg'

# needs to be added def encrypt(key, other)
# needs to be added def decrypt(key, other)
new_key()
#Private key is not being generated...	
