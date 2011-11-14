import types
from StringIO import StringIO

import gnupg

from django.core.files.base import File
from django.utils.translation import ugettext_lazy as _

from django_gpg.exceptions import GPGVerificationError, GPGSigningError, \
    GPGDecryptionError


KEY_TYPES = {
    'pub': _(u'Public'),
    'sec': _(u'Secret'),
}


class Key(object):
    @staticmethod
    def get_key_id(fingerprint):
        return fingerprint[-16:]

    @classmethod
    def get_all(cls, gpg, secret=False):
        result = []
        keys = gpg.gpg.list_keys(secret=secret)
        for key in keys:
            key_instance = Key(fingerprint=key['fingerprint'], uids=key['uids'], type=key['type'])
            key_instance.data = gpg.gpg.export_keys([key['keyid']], secret=secret)
            result.append(key_instance)

        return result

    @classmethod
    def get(cls, gpg, key_id, secret=False):
        if len(key_id) > 16:
            # key_id is a fingerpint
            key_id = Key.get_key_id(key_id)
            
        keys = gpg.gpg.list_keys(secret=secret)
        key = next((key for key in keys if key['keyid'] == key_id), None)
        key_instance = Key(fingerprint=key['fingerprint'], uids=key['uids'], type=key['type'])
        key_instance.data = gpg.gpg.export_keys([key['keyid']], secret=secret)

        return key_instance

    def __init__(self, fingerprint, uids, type):
        self.fingerprint = fingerprint
        self.uids = uids
        self.type = type

    @property
    def key_id(self):
        return Key.get_key_id(self.fingerprint)

    @property
    def user_ids(self):
        return u', '.join(self.uids)

    def __str__(self):
        return '%s "%s" (%s)' % (self.key_id, self.user_ids, KEY_TYPES.get(self.type, _(u'unknown')))

    def __unicode__(self):
        return unicode(self.__str__())

    def __repr__(self):
        return self.__unicode__()


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

    def sign_file(self, file_input, key=None, destination=None, key_id=None, passphrase=None, clearsign=False):
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

        if key:
            kwargs['keyid'] = key.key_id

        if passphrase:
            kwargs['passphrase'] = passphrase

        if isinstance(file_input, types.StringTypes):
            input_descriptor = open(file_input, 'rb')
        elif isinstance(file_input, types.FileType) or isinstance(file_input, File):
            input_descriptor = file_input
        elif issubclass(file_input.__class__, StringIO):
            input_descriptor = file_input
        else:
            raise ValueError('Invalid file_input argument type')

        if destination:
            output_descriptor = open(destination, 'wb')

        signed_data = self.gpg.sign_file(input_descriptor, **kwargs)
        if not signed_data.fingerprint:
            raise GPGSigningError('Unable to sign file')

        if destination:
            output_descriptor.write(signed_data.data)

        input_descriptor.close()

        if destination:
            output_descriptor.close()

        if not destination:
            return signed_data

    def decrypt_file(self, file_input):
        if isinstance(file_input, types.StringTypes):
            input_descriptor = open(file_input, 'rb')
        elif isinstance(file_input, types.FileType) or isinstance(file_input, File):
            input_descriptor = file_input
        else:
            raise ValueError('Invalid file_input argument type')

        result = self.gpg.decrypt_file(input_descriptor)
        input_descriptor.close()
        if not result.status:
            raise GPGDecryptionError('Unable to decrypt file')

        return result

    def create_key(self, *args, **kwargs):
        input_data = self.gpg.gen_key_input(**kwargs)
        fingerprint = self.gpg.gen_key(input_data)
        return Key.get(self.gpg, fingerprint)
        
