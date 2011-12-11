import types
from StringIO import StringIO
from pickle import dumps
import logging

import gnupg

from django.core.files.base import File
from django.utils.translation import ugettext_lazy as _

from queue_manager import Queue, QueuePushError

from django_gpg.exceptions import GPGVerificationError, GPGSigningError, \
    GPGDecryptionError, KeyDeleteError, KeyGenerationError, \
    KeyFetchingError, KeyDoesNotExist

logger = logging.getLogger(__name__)


KEY_TYPES = {
    'pub': _(u'Public'),
    'sec': _(u'Secret'),
}

KEY_CLASS_RSA = 'RSA'
KEY_CLASS_DSA = 'DSA'
KEY_CLASS_ELG = 'ELG-E'

KEY_PRIMARY_CLASSES = (
    ((KEY_CLASS_RSA), _(u'RSA')),
    ((KEY_CLASS_DSA), _(u'DSA')),
)

KEY_SECONDARY_CLASSES = (
    ((KEY_CLASS_RSA), _(u'RSA')),
    ((KEY_CLASS_ELG), _(u'Elgamal')),
)


class Key(object):
    @staticmethod
    def get_key_id(fingerprint):
        if len(fingerprint) > 16:
            # key_id is a fingerprint
            return fingerprint[-16:]
        else:
            return fingerprint

    @classmethod
    def get_all(cls, gpg, secret=False, exclude=None):
        result = []
        keys = gpg.gpg.list_keys(secret=secret)
        if exclude:
            excluded_id = exclude.key_id
        else:
            excluded_id = u''
        for key in keys:
            if not key['keyid'] in excluded_id:
                key_instance = Key(
                    fingerprint=key['fingerprint'],
                    uids=key['uids'],
                    type=key['type'],
                    data=gpg.gpg.export_keys([key['keyid']], secret=secret)
                )
                result.append(key_instance)

        return result

    @classmethod
    def get(cls, gpg, key_id, secret=False, search_keyservers=False):
        key_id = Key.get_key_id(key_id)
        keys = gpg.gpg.list_keys(secret=secret)
        key = next((key for key in keys if key['keyid'] == key_id), None)
        if not key:
            if search_keyservers and secret==False:
                try:
                    return gpg.receive_key(key_id)
                except KeyFetchingError:
                    raise KeyDoesNotExist
            else:
                raise KeyDoesNotExist

        key_instance = Key(
            fingerprint=key['fingerprint'],
            uids=key['uids'],
            type=key['type'],
            data=gpg.gpg.export_keys([key['keyid']], secret=secret)
        )

        return key_instance

    def __init__(self, fingerprint, uids, type, data):
        self.fingerprint = fingerprint
        self.uids = uids
        self.type = type
        self.data = data

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
    
    
    def uid_components(self, uid_index=0):
        uid = self.uids[uid_index]
        email_start = uid.find(u'<')
        if email_start:
            email_end = uid.find(u'>')
            email = uid[email_start + 1: email_end]
            uid = u''.join([uid[:email_start], uid[email_end + 1:]])
        else:
            email = None

        comment_start = uid.find(u'(')
        if comment_start:
            comment_end = uid.find(u')')
            comment = uid[comment_start + 1: comment_end]
            uid = u''.join([uid[:comment_start], uid[comment_end + 1:]])
        else:
            comment = None
            
        return uid.strip(), comment, email
    
    @property
    def name(self, uid_index=0):
        return self.uid_components(uid_index)[0]

    @property
    def comment(self, uid_index=0):
        return self.uid_components(uid_index)[1]

    @property
    def email(self, uid_index=0):
        return self.uid_components(uid_index)[2]


class GPG(object):
    def __init__(self, binary_path=None, home=None, keyring=None, keyservers=None):
        kwargs = {}
        if binary_path:
            kwargs['gpgbinary'] = binary_path

        if home:
            kwargs['gnupghome'] = home

        if keyring:
            kwargs['keyring'] = keyring

        self.keyservers = keyservers

        self.gpg = gnupg.GPG(**kwargs)

    def verify_file(self, file_input):
        """
        Verify the signature of a file.
        """
        if isinstance(file_input, types.StringTypes):
            descriptor = open(file_input, 'rb')
        elif isinstance(file_input, types.FileType) or isinstance(file_input, File) or isinstance(file_input, StringIO):
            descriptor = file_input
        else:
            raise ValueError('Invalid file_input argument type')

        verify = self.gpg.verify_file(descriptor)
        descriptor.close()
        if verify:
            return verify
        elif verify.status == 'no public key':
            # Exception to the rule, to be able to query the keyservers
            return verify
        else:
            raise GPGVerificationError(verify.status)

    def verify(self, data, retry=False):
        # TODO: try to merge with verify_file
        verify = self.gpg.verify(data)

        if verify:
            return verify
        else:
            if retry and verify.key_id:
                try:
                    logger.debug('key_id', verify.key_id)
                    self.receive_key(verify.keyid)
                except KeyFetchingError:
                    return verify
                else:
                    return self.verify(data)
            else:
                raise GPGVerificationError()

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

    def sign(self, data, key=None, key_id=None, passphrase=None, clearsign=False):
        kwargs = {}
        kwargs['clearsign'] = clearsign

        if key_id:
            kwargs['keyid'] = key_id

        if key:
            kwargs['keyid'] = key.key_id

        if passphrase:
            kwargs['passphrase'] = passphrase

        signed_data = self.gpg.sign(message=data, **kwargs)
        if not signed_data.fingerprint:
            raise GPGSigningError('Unable to sign data')
        return signed_data

    def decrypt_file(self, file_input):
        if isinstance(file_input, types.StringTypes):
            input_descriptor = open(file_input, 'rb')
        elif isinstance(file_input, types.FileType) or isinstance(file_input, File) or isinstance(file_input, StringIO):
            input_descriptor = file_input
        else:
            raise ValueError('Invalid file_input argument type')

        result = self.gpg.decrypt_file(input_descriptor)
        input_descriptor.close()
        if not result.status:
            raise GPGDecryptionError('Unable to decrypt file')

        return result

    def decrypt(self, data, passphrase=None):
        kwargs = {}
        if passphrase:
            kwargs['passphrase'] = passphrase

        result = self.gpg.decrypt(message=data, **kwargs)
        if not result.status:
            raise GPGDecryptionError('Unable to decrypt data')

        return result

    def create_key_background(self, *args, **kwargs):
        try:
            kwargs['gpg'] = dumps(self)
            queue = Queue(queue_name='gpg_key_gen', unique_names=True)
            queue.push(
                name=u''.join(
                    [
                        kwargs.get('name_real'),
                        kwargs.get('name_comment'),
                        kwargs.get('name_email'),
                    ]
                ),
                data=kwargs
            )
            return
        except QueuePushError:
            raise KeyGenerationError('A key with these same parameters is queued for creation')
        
    def create_key(self, *args, **kwargs):
        if kwargs.get('passphrase') == u'':
            kwargs.pop('passphrase')

        input_data = self.gpg.gen_key_input(**kwargs)
        key = self.gpg.gen_key(input_data)
        if not key:
            raise KeyGenerationError('Unable to generate key')

        return Key.get(self, key.fingerprint)

    def delete_key(self, key):
        status = self.gpg.delete_keys(key.fingerprint, key.type == 'sec').status
        if status == 'Must delete secret key first':
            self.delete_key(Key.get(self, key.fingerprint, secret=True))
            self.delete_key(key)
        elif status != 'ok':
            raise KeyDeleteError('Unable to delete key')

    def receive_key(self, key_id):
        for keyserver in self.keyservers:
            logger.debug('keyserver: %s' % keyserver)
            logger.debug('key_id: %s' % key_id)
            import_result = self.gpg.recv_keys(keyserver, key_id)
            if import_result:
                return Key.get(self, import_result.fingerprints[0], secret=False)

        raise KeyFetchingError
