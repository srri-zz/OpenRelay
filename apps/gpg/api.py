import os

import gnupg

from gpg.exceptions import GPGVerificationError


class GPG(object):
    def __init__(self, binary_path=None, home=None, keyring=None):
        kwargs = {}
        if binary_path:
            kwargs['gpgbinary'] = binary_path
        
        if home:
            kwargs['gnupghome'] = home
            
        if keyring:
            kwargs['keywring'] = keyring
            
        self.gpg = gnupg.GPG(**kwargs)

    def verify_file(self, filename):
        """
        Verify the signature of a file.
        """
        descriptor = open(filename, 'rb')
        verify = self.gpg.verify_file(descriptor)
        descriptor.close()
        if not verify:
            raise GPGVerificationError
            
        return True
        
    def verify(self, data):
        # TODO: try to merge with verify_file
        verify = self.gpg.verify(data)
        if not verify:
            raise GPGVerificationError
            
        return True
                

    def sign_file(self, filename, destination=None, key_id=None, passphrase=None):
        """
        Signs a filename, storing the signature and the original file 
        in the destination filename provided (the destination file is
        overrided if it already exists), if no destination file name is
        provided the signature is returned.
        """
        kwargs = {}
        if key_id:
            kwargs['keyid'] = key_id
            
        if passphrase:
            kwargs['passphrase'] = passphrase
        
        input_descriptor = open(filename, 'rb')
        
        if destination:
            output_descriptor = open(destination, 'wb')
        
        signed_data = self.gpg.sign_file(input_descriptor, **kwargs)
        
        if destination:
            output_descriptor.write(signed_data.data)
        
        input_descriptor.close()
        
        if destination:
            output_descriptor.close()

        if not destination:
            return signed_data.data
        
