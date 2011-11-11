import uuid
from datetime import datetime
from StringIO import StringIO

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile
from django.utils.simplejson import dumps, loads

import magic

from django_gpg import GPG, GPGVerificationError, GPGDecryptionError

from openrelay_resources.conf.settings import STORAGE_BACKEND
from openrelay_resources.literals import BINARY_DELIMITER, RESOURCE_SEPARATOR, \
    MAGIC_NUMBER

gpg = GPG()

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
    
    def full_name(self):
        return u'%s%c%s' % (self.uuid, '/', self.time_stamp)

    class Meta:
        abstract = True

        
class Resource(ResourceBase):
    file = models.FileField(upload_to='resources', storage=STORAGE_BACKEND(), verbose_name=_(u'file'))

    objects = ResourceManager()

    @staticmethod
    def encode_metadata(dictionary):
        json_data = dumps(dictionary)
        return r'%d%c%s' % (len(json_data), BINARY_DELIMITER, json_data)
        
    @staticmethod        
    def decode_metadata(data):
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
        delimiter_pos = data.find(r'%c' % BINARY_DELIMITER)
        json_size = int(data[len(MAGIC_NUMBER):delimiter_pos])
        return loads(data[delimiter_pos + 1:delimiter_pos + 1 + json_size]), delimiter_pos + 1 + json_size

    @staticmethod
    def get_fake_upload_to(return_value):
        return lambda instance, filename: unicode(return_value)

    def save(self, key, *args, **kwargs):
        name = kwargs.pop('name', None)
        if not name:
            name = self.file.name

        uuid = RESOURCE_SEPARATOR.join([key, name])
        
        metadata = {
            'uuid': uuid,
        }
        
        container = StringIO()
        container.write(MAGIC_NUMBER)
        container.write(Resource.encode_metadata(metadata))
        container.write(self.file.file.read())
        container.seek(0)
        
        signature = gpg.sign_file(container, key=kwargs.get('key', None))
        self.file.file = ContentFile(signature.data)

        self.file.field.generate_filename = Resource.get_fake_upload_to('%s_%s' % (uuid, signature.timestamp))
        self.uuid = uuid
        self.time_stamp = int(signature.timestamp)
        
        container.close()
        super(Resource, self).save(*args, **kwargs)

    def exists(self):
        return self.file.storage.exists(self.uuid)

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
            return None, None
        except IOError:
            return None, None
       
    @property
    def metadata(self):
        return self.decode_resource()[0]
        
    def _verify(self):
        if not self.file.name:
            return False

        try:
            descriptor = self.open()
            return gpg.verify_file(descriptor)
        except IOError:
            return None

    @property
    def is_valid(self):
        try:
            if self._verify():
                return True
            else:
                return None
        except GPGVerificationError:
            return False

    @property
    def raw_timestamp(self):
        try:
            verify = self._verify()
            return int(verify.sig_timestamp)
        except GPGVerificationError:
            return None
            
    @property
    def timestamp(self):
        return datetime.fromtimestamp(self.raw_timestamp)
        
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
       
    @property
    def fingerprint(self):
        try:
            verify = self._verify()
            return verify.fingerprint
        except GPGVerificationError:
            return None       

    @property
    def key_id(self):
        try:
            verify = self._verify()
            return verify.key_id
        except GPGVerificationError:
            return None     
            
    @property
    def signature_id(self):
        try:
            verify = self._verify()
            return verify.signature_id
        except GPGVerificationError:
            return None                
            
    @property
    def username(self):
        try:
            verify = self._verify()
            return verify.username
        except GPGVerificationError:
            return None                 

    @property
    def signature_status(self):
        try:
            verify = self._verify()
            return verify.status
        except GPGVerificationError:
            return None
            
    @models.permalink
    def get_absolute_url(self):
        return ('resource_serve', [self.uuid, self.time_stamp])
      
            
    class Meta(ResourceBase.Meta):
        ordering = ('-time_stamp', )
        verbose_name = _(u'resource')
        verbose_name_plural = _(u'resources')

