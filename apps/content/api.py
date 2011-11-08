import uuid
import os

from django.core.files.storage import FileSystemStorage
from django.core.files.base import ContentFile

from core.runtime import gpg


class ContentCache(object):
    def __init__(self, path):
        self.path = path
        self.storage = FileSystemStorage(location=path)

    def open(self, filename):
        return self.storage.open(filename)
    

class ContentStorage(object):
    """
    Defines the storage class for the resources
    """
    def __init__(self, path, content_cache):
        self.path = path
        self.storage = FileSystemStorage(location=path)
        self.content_cache = content_cache
        
    def save(self, filename, content):
        self.storage.save(filename, content)
        
    def store(self, resource):
        """
        Store a resource in a ContentCache, compliments the 
        functionality of the Resource class 'store' method 
        """ 
        resource_content = resource.open()
        self.save(resource.uuid, resource_content)
        resource_content.close()
        
    def retrieve(self, resource_id):
        resource = Storage.open(resource_id)
        if gpg.verify(resource):
            return resource


class Resource(object):
    def __init__(self, filename):
        """
        Take a supplied file and turn it into an OpenRelay resource
        """
        self.id = unicode(uuid.uuid4())
        self.data = gpg.sign_file(filename)
        
    def open(self):
        """
        Returns a file-like object to the resource data
        """
        return ContentFile(self.data)

    def store(self, content_cache):
        """
        Store the resource in the provided instance of a ContentCache
        Class
        """
        resource_content = self.open()
        content_cache.save(self.id, resource_content)
        resource_content.close()
