import urlparse
from datetime import datetime
from StringIO import StringIO

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.files.base import ContentFile
from django.utils.simplejson import dumps, loads
from django.core.urlresolvers import reverse

import magic

from django_gpg import GPG, Key, GPGVerificationError, GPGDecryptionError, KeyFetchingError

from openrelay_resources.conf.settings import STORAGE_BACKEND
from openrelay_resources.literals import BINARY_DELIMITER, RESOURCE_SEPARATOR, \
    MAGIC_NUMBER, TIME_STAMP_SEPARATOR, MAGIC_VERSION
from openrelay_resources.exceptions import ORInvalidResourceFile
from openrelay_resources.filters import FilteredHTML, FilterError

from core.runtime import gpg


class ResourceManager(models.Manager):
    def get(self, *args, **kwargs):
        try:
            return super(ResourceManager, self).get(*args, **kwargs)
        except self.model.MultipleObjectsReturned:
            uuid = kwargs.pop('uuid')
            return super(ResourceManager, self).get_query_set().filter(uuid=uuid)[0]


class ResourceBase(models.Model):
    uuid = models.CharField(max_length=48, blank=True, editable=False, verbose_name=_(u'UUID'))
    time_stamp = models.PositiveIntegerField(verbose_name=_(u'timestamp'))

    def __unicode__(self):
        return self.uuid

    @property
    def full_name(self):
        return u'%s%c%s' % (self.uuid, TIME_STAMP_SEPARATOR, self.time_stamp)

    class Meta:
        abstract = True


class Resource(ResourceBase):
    file = models.FileField(upload_to='resources', storage=STORAGE_BACKEND(), verbose_name=_(u'file'))

    objects = ResourceManager()


    @staticmethod
    def prepare_resource_uuid(key, filename):
        return RESOURCE_SEPARATOR.join([key, filename])
    
    @staticmethod
    def prepare_resource_url(key, filename):
        return urlparse.urljoin(reverse('resource_serve'), Resource.prepare_resource_uuid(key, filename))

    @staticmethod
    def encode_metadata(dictionary):
        json_data = dumps(dictionary)
        return r'%d%c%s' % (len(json_data), BINARY_DELIMITER, json_data)

    @staticmethod
    def decode_metadata(data):
        # Stream implementation, disabled until stream based processing
        # is added
        '''
        #section = SECTION_LENGTH
        size = ''
        #metadata = ''

        while True:
            char = descriptor.read(1)
            #if section == SECTION_LENGTH:
            if char == '%c' % 0x00:
                #section = SECTION_METADATA
                size = int(size)
                print 'size', size
                descriptor.read(1)
                metadata = read(size)
                break
            else:
                size =+ char
        return loads(metadata)
        '''
        
        try:
            magic_end = data.index(r'%c' % BINARY_DELIMITER)
            if data[:magic_end] != MAGIC_NUMBER:
                raise ORInvalidResourceFile('Invalid magic number')

            version_end = data.find(r'%c' % BINARY_DELIMITER, magic_end + 1)
            if data[magic_end + 1:version_end] != '1':
                raise ORInvalidResourceFile('Invalid/unknown resource file format version')
            
            size_end = data.find(r'%c' % BINARY_DELIMITER, version_end + 1)
            json_size = int(data[version_end + 1:size_end])
            return loads(data[size_end + 1:size_end + 1 + json_size]), size_end + 1 + json_size
        except ValueError:
            raise ORInvalidResourceFile('Magic number, version or metadata markers not found')


    @staticmethod
    def get_fake_upload_to(return_value):
        return lambda instance, filename: unicode(return_value)
        
    def __init__(self, *args, **kwargs):
        super(Resource, self).__init__(*args, **kwargs)
        self.properties = {}

    def save(self, key, *args, **kwargs):
        name = kwargs.pop('name', None)
        if not name:
            name = self.file.name

        uuid = Resource.prepare_resource_uuid(key, name)
        metadata = {
            'uuid': uuid,
            'filename': self.file.name,
        }

        container = StringIO()
        container.write(MAGIC_NUMBER)
        container.write(r'%c' % BINARY_DELIMITER)
        container.write(MAGIC_VERSION)
        container.write(r'%c' % BINARY_DELIMITER)
        container.write(Resource.encode_metadata(metadata))
        if kwargs.pop('filter_html'):
            try:
                container.write(FilteredHTML(self.file.file.read(), url_filter=lambda x: Resource.prepare_resource_url(key, x)))
            except FilterError:
                self.file.file.seek(0)
                container.write(self.file.file.read())
        else:
            container.write(self.file.file.read())
        container.seek(0)

        signature = gpg.sign_file(container, key=Key.get(gpg, key))
        self.file.file = ContentFile(signature.data)

        self.file.field.generate_filename = Resource.get_fake_upload_to('%s%c%s' % (uuid, TIME_STAMP_SEPARATOR, signature.timestamp))
        self.uuid = uuid
        self.time_stamp = int(signature.timestamp)

        container.close()
        super(Resource, self).save(*args, **kwargs)
        return self

    def exists(self):
        return self.file.storage.exists(self.full_name)

    def delete(self, *args, **kwargs):
        self.file.storage.delete(self.uuid)
        super(Resource, self).delete(*args, **kwargs)

    def decode_resource(self):
        try:
            descriptor = self.open()
            result = gpg.decrypt_file(descriptor)
            metadata, metadata_size = Resource.decode_metadata(result.data)
            content = result.data[metadata_size:]
            return metadata, content
        except GPGDecryptionError:
            #TODO: research: return None or an empty dictionary {}
            return None, None
        except IOError:
            #TODO: research: return None or an empty dictionary {}
            return None, None
        except ORInvalidResourceFile, error:
            #TODO: research: return error string or {'error':error}
            return error, error

    @property
    def metadata(self):
        return self.decode_resource()[0]
            
    @property
    def real_uuid(self):
        try:
            descriptor = self.open()
            result = gpg.decrypt_file(descriptor)
            metadata, metadata_size = Resource.decode_metadata(result.data)
            return u'%s%c%s' % (self.fingerprint, RESOURCE_SEPARATOR, metadata['filename'])
        except GPGDecryptionError:
            return None
        except IOError:
            return None
        except ORInvalidResourceFile, error:
            return error

    def _verify(self):
        if not self.file.name:
            return False

        try:
            descriptor = self.open()
            verify = gpg.verify_file(descriptor)
            if verify.status == 'no public key':
                # Try to fetch the public key from the keyservers
                try:
                    gpg.receive_key(verify.key_id)
                    return self._verify()
                except KeyFetchingError:
                    return verify
            else:
                return verify
        except IOError:
            return None

    def _refresh_properties(self):
        try:
            verify = self._verify()
            if verify:
                self.properties = {
                    'signature_status': verify.status,
                    'username': verify.username,
                    'signature_id': verify.signature_id,
                    'key_id': verify.key_id,
                    'fingerprint': verify.fingerprint,
                    'is_valid': True,
                    'raw_timestamp': verify.sig_timestamp,
                    'timestamp': datetime.fromtimestamp(int(verify.sig_timestamp)),
                }
            else:
                self.properties = {
                    'signature_status': verify.status,
                    'username': verify.username,
                    'signature_id': None,
                    'key_id': verify.key_id,
                    'fingerprint': None,
                    'is_valid': False,
                    'raw_timestamp': None,
                    'timestamp': None,
                }
        except GPGVerificationError, msg:
            self.properties = {
                'signature_status': msg,
                'username': None,
                'signature_id': None,
                'key_id': None,
                'fingerprint': None,
                'is_valid': False,
                'raw_timestamp': None,
                'timestamp': None,
            }

    def __getattr__(self, name):
        attribute_list = ['is_valid', 'signature_status', 'username', 'signature_id', 'raw_timestamp', 'timestamp', 'fingerprint', 'key_id']
        if name in attribute_list:
            try:
                return self.properties[name]
            except KeyError:
                self._refresh_properties()
                return self.properties[name]
        else:
            raise AttributeError, name                

    def open(self):
        """
        Returns a file-like object to the resource data
        """
        return self.file.storage.open(self.file.name)

    def extract(self):
        return self.decode_resource()[1]

    @property
    def mimetype(self):
        magic_mime = magic.Magic(mime=True)
        magic_encoding = magic.Magic(mime_encoding=True)

        content = self.decode_resource()[1]
        if content:
            mimetype = magic_mime.from_buffer(content)
            encoding = magic_encoding.from_buffer(content)
            return mimetype, encoding
        else:
            return u'', u''

    @models.permalink
    def get_absolute_url(self):
        return ('resource_serve', [self.uuid, self.time_stamp])

    class Meta(ResourceBase.Meta):
        ordering = ('-time_stamp', )
        verbose_name = _(u'resource')
        verbose_name_plural = _(u'resources')
