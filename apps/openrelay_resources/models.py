import errno
import logging
import urlparse
import codecs

from datetime import datetime

try:
    from cStringIO import StringIO
except ImportError:
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
from openrelay_resources.conf.settings import STORAGE_SIZE_LIMIT
from openrelay_resources.literals import BINARY_DELIMITER, RESOURCE_SEPARATOR, \
    MAGIC_NUMBER, TIMESTAMP_SEPARATOR, MAGIC_VERSION
from openrelay_resources.exceptions import ORInvalidResourceFile
from openrelay_resources.filters import FilteredHTML, FilterError
from openrelay_resources.managers import ResourceManager

from core.runtime import gpg


class ResourceBase(models.Model):
    uuid = models.CharField(max_length=48, blank=True, editable=False, verbose_name=_(u'UUID'))
    
    class LatestVersionCache(object):
        pk = None
    
    _latest_version_cache = LatestVersionCache()

    def latest_version(self):
        latest_version_instance = getattr(self, u''.join([self.resource_version_model_name.lower(), '_set'])).order_by('-timestamp')[0]

        if latest_version_instance.pk != self._latest_version_cache.pk:
            self._latest_version_cache = latest_version_instance
        
        return self._latest_version_cache

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
        try:
            resource = getattr(self, self.parent_resource_model_name.lower())
        except Resource.DoesNotExist:
            # Orphan version instance, delete it
            self.delete()
            return '<Invalid version instance>'
        return VersionBase.prepare_full_resource_name(resource.uuid, self.timestamp)

    def __unicode__(self):
        return self.full_uuid

    class Meta:
        abstract = True
        ordering = ('-timestamp',)


class Resource(ResourceBase):
    resource_version_model_name = u'Version'

    @staticmethod
    def storage_culling():
        used_size = Resource.storage_used_space()
        while used_size > STORAGE_SIZE_LIMIT:
            for version in Version.objects.order_by('last_access'):
                version_size = version.size
                if version_size:
                    version.delete()
                    # If there are no more versions of this resource
                    # delete the resource
                    if Version.objects.filter(resource=version.resource).count() == 0:
                        version.resource.delete()
                    used_size -= version_size
            
        return used_size

    @staticmethod
    def storage_used_space():
        total_space = 0
        for version in Version.objects.all():
            total_space += version.size
        
        return total_space
        
    @staticmethod
    def prepare_resource_uuid(key, name):
        return RESOURCE_SEPARATOR.join([key.fingerprint, name])
        
    @models.permalink
    def get_absolute_url(self):
        return ('resource_serve', [self.uuid])
    
    def upload(self, *args, **kwargs):
        uncompress = kwargs.pop('uncompress')
        usefilename = kwargs.pop('usefilename', None)
        version = kwargs.pop('raw_data_version', None)

        if not version:
            key = kwargs.pop('key')
            file = kwargs.pop('file')
            label = kwargs.pop('label')

            description = kwargs.pop('description')
            filter_html= kwargs.pop('filter_html')
           
            if usefilename:
                name = kwargs.pop('name', None)
            else:
                namepop = kwargs.pop('name', None)
                name = None

            if not name:
                name = file.name
                    
            uuid = Resource.prepare_resource_uuid(key, name)
        else:
            uuid = version.verified_uuid

        try:
            resource = Resource.objects.get(uuid=uuid)
            self.pk = resource.pk
            self.uuid = uuid
            self.save(*args, **kwargs)
        except Resource.DoesNotExist:
            self.uuid = uuid
            self.save(*args, **kwargs)
            resource = self
        
        if version:
            version.resource = resource
            version.upload()
        else:
            version = Version(resource=resource, file=file)
            version.upload(key=key, name=name, label=label, description=description, filter_html=filter_html)
    
    class Meta(ResourceBase.Meta):
        verbose_name = _(u'resource')
        verbose_name_plural = _(u'resources')


class Version(VersionBase):
    parent_resource_model_name = u'Resource'
    
    resource = models.ForeignKey(Resource, verbose_name=_(u'resource'))
    file = models.FileField(upload_to='resources', storage=STORAGE_BACKEND(), verbose_name=_(u'file'), editable=False)
    last_access = models.DateTimeField(verbose_name=_(u'last access'), editable=False)

    @staticmethod
    def prepare_resource_url(key, filename):
        #return urlparse.urljoin(reverse('resource_serve', args=[Resource.prepare_resource_uuid(key.fingerprint, filename)]))
        return reverse('resource_serve', args=[Resource.prepare_resource_uuid(key, filename)])

    @staticmethod
    def encode_metadata(dictionary):
        json_data = dumps(dictionary)
        return r'%d%c%s' % (len(json_data), BINARY_DELIMITER, json_data)

    @staticmethod
    def get_fake_upload_to(return_value):
        return lambda instance, filename: unicode(return_value)

    @classmethod
    def create_from_raw(cls, data):
        version = cls()
        version._raw = data
        version._refresh_signature_properties()
        # TODO: better verification method
        # TODO: pass exceptions to caller
        if version.verify:
            resource = Resource()
            resource.upload(raw_data_version=version)
            return version
        else:
            raise ORInvalidResourceFile('Remote resource failed verification')

    def __init__(self, *args, **kwargs):
        super(Version, self).__init__(*args, **kwargs)
        self._signature_properties = {}
        self._metadata = {}
        self._content = None
        self._raw = None

    def upload(self, key=None, *args, **kwargs):
        if self.pk:
            raise NotImplemented('Cannot update an existing resource, create a new version from the same content instead.')

        if not self._raw:
            name = kwargs.pop('name', None)
            if not name:
                name = self.file.name

            self._metadata = {
                'name': name,
            }

            label = kwargs.pop('label')
            if label:
                self._metadata['label'] = label

            description = kwargs.pop('description')
            if description:
                self._metadata['description'] = description

            container = StringIO()
            wrapper = codecs.getwriter('utf8')(container)
            container.write(MAGIC_NUMBER)
            container.write(r'%c' % BINARY_DELIMITER)
            container.write(MAGIC_VERSION)
            container.write(r'%c' % BINARY_DELIMITER)
            container.write(Version.encode_metadata(self._metadata))

            if kwargs.pop('filter_html'):
                try:
                    self.file.file.seek(0)
                    output = FilteredHTML(self.file.file.read(), url_filter=lambda x: Version.prepare_resource_url(key, x)).html
                    wrapper.writelines(output)
                except FilterError:
                    self.file.file.seek(0)
                    container.write(self.file.file.read())
            else:
                container.write(self.file.file.read())

            container.seek(0)
            signature = gpg.sign_file(container, key)
            container.close()
            self.timestamp = int(signature.timestamp)
            self.file.file = ContentFile(signature.data)
            # Add slugify to sanitize the final filename
            self.file.field.generate_filename = Version.get_fake_upload_to(slugify(Version.prepare_full_resource_name(self.resource.uuid, signature.timestamp)))
        else:
            self.file.field.generate_filename = Version.get_fake_upload_to(slugify(Version.prepare_full_resource_name(self.verified_uuid, self.raw_timestamp)))
            self.file.save(self.verified_uuid, ContentFile(self._raw.encode('UTF-8')), save=False)
            self.timestamp = self.raw_timestamp

        self.last_access = datetime.now()
        self.save(*args, **kwargs)

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
        if not self.file.name and not self._raw:
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
                self.verify = verify
                if verify:
                    self._signature_properties = {
                        'signature_status': verify.status,
                        'username': verify.username,
                        'signature_id': verify.signature_id,
                        'key_id': verify.key_id,
                        'fingerprint': verify.fingerprint,
                        'is_valid': True,
                        'raw_timestamp': verify.sig_timestamp,
                        'timestamp_display': datetime.fromtimestamp(int(verify.sig_timestamp)),
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
                        'timestamp_display': None,
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
                    'timestamp_display': None,
                }

    def __getattr__(self, name):
        signature_properties_list = ['is_valid', 'signature_status', 'username', 'signature_id', 'raw_timestamp', 'timestamp_display', 'fingerprint', 'key_id']
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

    @property
    def content(self):
        # Returns the plain text content of a resource
        self._refresh_metadata()
        self.last_access = datetime.now()
        self.save()
        return self._content
        
    def download(self):
        # Returns a file like object to the signed resource
        self.last_access = datetime.now()
        self.save()
        return self.open()

    @property
    def metadata(self):
        self._refresh_metadata()
        return self._metadata

    @property
    def signature_properties(self):
        self._refresh_signature_properties()
        return self._signature_properties

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

    # Storage methods
    def open(self):
        """
        Returns a file-like object to the resource's raw data
        """
        if self._raw:
            container = StringIO()
            container.write(self._raw)
            container.seek(0)
            return container
        else:
            return self.file.storage.open(self.file.name)

    def exists(self):
        return self.file.storage.exists(self.file.name)

    @property
    def size(self):
        return self.file.storage.size(self.file.name)

    def delete(self, *args, **kwargs):
        # Delete using filename not uuid as 
        # there is no warraty the uuid is formed as a valid filename
        self.file.storage.delete(self.file.name)
        
        super(Version, self).delete(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('resource_serve', [self.full_uuid])

    class Meta(VersionBase.Meta):
        verbose_name = _(u'version')
        verbose_name_plural = _(u'versions')
