import os
import types

import gnupg

from django.core.files.base import File

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

    def verify_file(self, file_input):
        """
        Verify the signature of a file.
        """
        if isinstance(file_input, types.StringTypes):
            descriptor = open(file_input, 'rb')
        elif isinstance(file_input, types.FileType) or isinstance(file_input, File):
            descriptor = file_input
        else:
            raise ValueError('Invalid file_input argument type')
            
        verify = self.gpg.verify_file(descriptor)
        descriptor.close()
        if verify:
            return verify
        else:
            raise GPGVerificationError('Signature could not be verified!')
        
    def verify(self, data):
        # TODO: try to merge with verify_file
        verify = self.gpg.verify(data)

        if verify:
            return verify
        else:
            raise GPGVerificationError('Signature could not be verified!')            
                

    def sign_file(self, file_input, destination=None, key_id=None, passphrase=None, clearsign=False):
        """
        Signs a filename, storing the signature and the original file 
        in the destination filename provided (the destination file is
        overrided if it already exists), if no destination file name is
        provided the signature is returned.
        """
        kwargs = {}
        kwargs['clearsign'] = clearsign
        
        if key_id:
            kwargs['keyid'] = key_id
            
        if passphrase:
            kwargs['passphrase'] = passphrase

        if isinstance(file_input, types.StringTypes):
            input_descriptor = open(file_input, 'rb')
        elif isinstance(file_input, types.FileType) or isinstance(file_input, File):
            input_descriptor = file_input
        else:
            raise ValueError('Invalid file_input argument type')
        
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
        
            
    def decrypt_file(self, file_input):
        if isinstance(file_input, types.StringTypes):
            input_descriptor = open(file_input, 'rb')
        elif isinstance(file_input, types.FileType) or isinstance(file_input, File):
            input_descriptor = file_input
        else:
            raise ValueError('Invalid file_input argument type')        
        
        result = self.gpg.decrypt_file(input_descriptor)
        
        input_descriptor.close()
        
        return result
        
