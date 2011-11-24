import urlparse
from datetime import datetime
from StringIO import StringIO

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.files.base import ContentFile
from django.utils.simplejson import dumps, loads
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from django.core.exceptions import ValidationError

import magic

from django_gpg import Key, GPGVerificationError, GPGDecryptionError, KeyFetchingError

from openrelay_resources.conf.settings import STORAGE_BACKEND
from openrelay_resources.literals import BINARY_DELIMITER, RESOURCE_SEPARATOR, \
    MAGIC_NUMBER, TIMESTAMP_SEPARATOR, MAGIC_VERSION
from openrelay_resources.exceptions import ORInvalidResourceFile
from openrelay_resources.filters import FilteredHTML, FilterError
from openrelay_resources.managers import ResourceManager

from core.runtime import gpg


class ResourceBase(models.Model):
    uuid = models.CharField(max_length=48, blank=True, editable=False, verbose_name=_(u'UUID'))

    def latest_version(self):
        return self.version_set.order_by('-timestamp')[0]

    def __getattr__(self, name):
        # If an attribute is not found for the Resource instance
        # try the Version instance
        return getattr(self.latest_version(), name)

    @property
    def verified_uuid(self):
        return self.latest_version().verified_uuid

    def __unicode__(self):
        return self.uuid


    def clean(self):
        # Don't allow timestamp separators in the filename or resource name
        if TIMESTAMP_SEPARATOR in self.uuid:
            raise ValidationError('timestamp separators are not allows in the uuid or as part of the resource name')
            
    class Meta:
        abstract = True

    objects = ResourceManager()


class VersionBase(models.Model):
    timestamp = models.PositiveIntegerField(verbose_name=_(u'timestamp'), db_index=True, editable=False)

    @staticmethod
    def prepare_full_resource_name(uuid, timestamp):
        return u'%s%c%s' % (uuid, TIMESTAMP_SEPARATOR, timestamp)

    @property
    def full_uuid(self):
        return VersionBase.prepare_full_resource_name(self.resource.uuid, self.timestamp)

    def __unicode__(self):
        return self.full_uuid

    class Meta:
        abstract = True
        ordering = ('-timestamp',)


class Resource(ResourceBase):
    @staticmethod
    def prepare_resource_uuid(key, name):
        return RESOURCE_SEPARATOR.join([key.fingerprint, name])
        
    @models.permalink
    def get_absolute_url(self):
        return ('resource_serve', [self.uuid])
        
    def save(self, *args, **kwargs):
        key = kwargs.pop('key')
        file = kwargs.pop('file')
        label = kwargs.pop('label')
        description = kwargs.pop('description')
        filter_html= kwargs.pop('filter_html')
        
        name = kwargs.pop('name', file.name)
                    
        uuid = Resource.prepare_resource_uuid(key, name)
        try:
            resource = Resource.objects.get(uuid=uuid)
            self.pk = resource.pk
            self.uuid = resource.uuid
            super(Resource, self).save(*args , **kwargs)
        except Resource.DoesNotExist:
            self.uuid = uuid
            super(Resource, self).save(*args , **kwargs)
            resource = self
        
        version = Version(resource=resource, file=file)
        version.save(key=key, name=name, label=label, description=description, filter_html=filter_html)
    
    class Meta(ResourceBase.Meta):
        verbose_name = _(u'resource')
        verbose_name_plural = _(u'resources')


class Version(VersionBase):
    resource = models.ForeignKey(Resource, verbose_name=_(u'resource'))
    file = models.FileField(upload_to='resources', storage=STORAGE_BACKEND(), verbose_name=_(u'file'), editable=False)

    @staticmethod
    def prepare_resource_url(key, filename):
        return urlparse.urljoin(reverse('resource_serve'), Resource.prepare_resource_uuid(key.fingerprint, filename))

    @staticmethod
    def encode_metadata(dictionary):
        json_data = dumps(dictionary)
        return r'%d%c%s' % (len(json_data), BINARY_DELIMITER, json_data)

    @staticmethod
    def get_fake_upload_to(return_value):
        return lambda instance, filename: unicode(return_value)

    def __init__(self, *args, **kwargs):
        super(Version, self).__init__(*args, **kwargs)
        self._signature_properties = {}
        self._metadata = {}
        self._content = None

    def save(self, key, *args, **kwargs):
        if self.pk:
            raise NotImplemented('Cannot update an existing resource, create a new version from the same content instead.')

        name = kwargs.pop('name', None)
        if not name:
            name = self.file.name

        metadata = {
            'name': name,
        }

        label = kwargs.pop('label')
        if label:
            metadata['label'] = label

        description = kwargs.pop('description')
        if description:
            metadata['description'] = description

        container = StringIO()
        container.write(MAGIC_NUMBER)
        container.write(r'%c' % BINARY_DELIMITER)
        container.write(MAGIC_VERSION)
        container.write(r'%c' % BINARY_DELIMITER)
        container.write(Version.encode_metadata(metadata))
        if kwargs.pop('filter_html'):
            try:
                container.write(FilteredHTML(self.file.file.read(), url_filter=lambda x: Version.prepare_resource_url(key, x)))
            except FilterError:
                self.file.file.seek(0)
                container.write(self.file.file.read())
        else:
            container.write(self.file.file.read())
        container.seek(0)

        signature = gpg.sign_file(container, key)
        self.file.file = ContentFile(signature.data)

        # Added slugify to sanitize the final filename
        self.file.field.generate_filename = Version.get_fake_upload_to(slugify(Version.prepare_full_resource_name(self.resource.uuid, signature.timestamp)))
        self.timestamp = int(signature.timestamp)

        container.close()
        super(Version, self).save(*args, **kwargs)

    def exists(self):
        return self.file.storage.exists(self.file.name)

    def delete(self, *args, **kwargs):
        # Delete using filename not uuid as 
        # there is no warraty the uuid is formed as a valid filename
        self.file.storage.delete(self.file.name)
        super(Version, self).delete(*args, **kwargs)

    def _refresh_metadata(self):
        if not self._metadata:
            try:
                descriptor = self.open()
                result = gpg.decrypt_file(descriptor)
                self._decode_result(result.data)
            except (GPGDecryptionError, IOError):
                self._metadata = None
                self._content = None
            except ORInvalidResourceFile:
                self._metadata = None
                self._content = None

    def _decode_result(self, data):
        # TODO: Change to a regex
        try:
            magic_end = data.index(r'%c' % BINARY_DELIMITER)
            if data[:magic_end] != MAGIC_NUMBER:
                raise ORInvalidResourceFile('Invalid magic number')

            # TODO: Change all find instances to index?
            version_end = data.find(r'%c' % BINARY_DELIMITER, magic_end + 1)
            if data[magic_end + 1:version_end] != '1':
                raise ORInvalidResourceFile('Invalid/unknown resource file format version')

            size_end = data.find(r'%c' % BINARY_DELIMITER, version_end + 1)
            json_size = int(data[version_end + 1:size_end])
            self._content = data[size_end + 1 + json_size:]
            self._metadata = loads(data[size_end + 1:size_end + 1 + json_size])
        except ValueError:
            raise ORInvalidResourceFile('Magic number, version or metadata markers not found')

    @property
    def verified_uuid(self):
        try:
            return u'%s%c%s' % (self.fingerprint, RESOURCE_SEPARATOR, self.name)
        except GPGDecryptionError:
            return None
        except IOError:
            return None
        except ORInvalidResourceFile, error:
            return error
        except KeyError:
            ORInvalidResourceFile('UUID verification error')

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
            return False

    def _refresh_signature_properties(self):
        if not self._signature_properties:
            try:
                verify = self._verify()
                if verify:
                    self._signature_properties = {
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
                    self._signature_properties = {
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
                self._signature_properties = {
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
        signature_properties_list = ['is_valid', 'signature_status', 'username', 'signature_id', 'raw_timestamp', 'timestamp', 'fingerprint', 'key_id']
        metadata_attributes_list = ['name', 'label', 'description']
        
        if name in signature_properties_list:
            try:
                self._refresh_signature_properties()
                return self._signature_properties[name]
            except KeyError, msg:
                # Convert KeyError excepetion into an AttributeError
                # as we are simulating class properties
                raise AttributeError(msg)
        elif name in metadata_attributes_list:
            self._refresh_metadata()
            # Don't raise KeyError or AttributeError exception for a
            # non existant value on 'label' or 'description' as these are
            # blank by default 
            return self._metadata.get(name, u'')
        else:
            raise AttributeError

    def open(self):
        """
        Returns a file-like object to the resource data
        """
        return self.file.storage.open(self.file.name)

    @property
    def content(self):
        self._refresh_metadata()
        return self._content

    @property
    def metadata(self):
        self._refresh_metadata()
        return self._metadata

    @property
    def mimetype(self):
        magic_mime = magic.Magic(mime=True)
        magic_encoding = magic.Magic(mime_encoding=True)

        content = self.content
        if content:
            mimetype = magic_mime.from_buffer(content)
            encoding = magic_encoding.from_buffer(content)
            return mimetype, encoding
        else:
            return u'', u''

    @models.permalink
    def get_absolute_url(self):
        return ('resource_serve', [self.full_uuid])

    class Meta(VersionBase.Meta):
        verbose_name = _(u'version')
        verbose_name_plural = _(u'versions')
