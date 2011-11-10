import hashlib
import uuid
from datetime import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile

import magic

#from core.runtime import gpg
from gpg import GPG
from gpg.exceptions import GPGVerificationError

from content.conf.settings import STORAGE_BACKEND

gpg = GPG()

HASH_FUNCTION = lambda x: hashlib.sha256(x).hexdigest()

def get_fake_upload_to(return_value):
    return lambda instance, filename: unicode(return_value)


class Resource(models.Model):
    file = models.FileField(upload_to='resources', storage=STORAGE_BACKEND(), verbose_name=_(u'file'))
    uuid = models.CharField(max_length=48, blank=True, editable=False)
    
    def __unicode__(self):
        return self.uuid

    def save(self, *args, **kwargs):
        signature = gpg.sign_file(self.file.file)
        self.file.file = ContentFile(signature)
        hash_value = HASH_FUNCTION(signature)
        
        self.file.field.generate_filename = get_fake_upload_to(hash_value)
        #self.file.field.upload_to = fake_upload_to
        self.uuid = hash_value
        
        super(Resource, self).save(*args, **kwargs)
        
        '''
        #if not self.pk:
        #    self.uuid = unicode(uuid.uuid4())
        #print self.file.name
        
            
        #descriptor = self.file.file
        #descriptor.seek(0)
        ##self.file = ContentFile(content=gpg.sign_file(descriptor=descriptor))
        #self.file.name='sd'
        super(Resource, self).save(*args, **kwargs)
        
        self.uuid = self.file.name
        #descriptor = self.file.file
        
    
        #descriptor.seek(0)
        descriptor = self.file.storage.open(name=self.file.name)
        #print gpg.sign_file(descriptor=descriptor)
        signature = gpg.sign_file(descriptor=descriptor)
        descriptor.close()
        print self.uuid
        self.file.storage.save(self.uuid, ContentFile(signature))
        #self.file.content = ContentFile(gpg.sign_file(descriptor=descriptor))
        
        super(Resource, self).save(*args, **kwargs)
        
        #self.save()
        '''
    def exists(self):
        return self.file.storage.exists(self.uuid)
        
    def _verify(self):
        if not self.file.name:
            return False
            
        descriptor = self.file.storage.open(name=self.file.name)
        return gpg.verify_file(descriptor)

    @property
    def is_valid(self):
        try:
            self._verify()
            return True
        except GPGVerificationError:
            return False
            
    @property
    def timestamp(self):
        try:
            verify = self._verify()
            return datetime.fromtimestamp(int(verify.sig_timestamp))
        except GPGVerificationError:
            return None
        
    def open(self):
        """
        Returns a file-like object to the resource data
        """
        return self.file.storage.open(self.file.name)
        
    @property
    def mimetype(self):
        magic_mime = magic.Magic(mime=True)
        magic_encoding = magic.Magic(mime_encoding=True)
        
        descriptor = self.open()
        
        result = gpg.decrypt_file(descriptor)

        mimetype = magic_mime.from_buffer(result.data)
        encoding = magic_encoding.from_buffer(result.data)
        return mimetype, encoding
       
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

    #def store(self, content_cache):
    #    """
    #    Store the resource in the provided instance of a ContentCache
    #    Class
    #    """
    #    resource_content = self.open()
    #    content_cache.save(self.id, resource_content)
    #    resource_content.close()
