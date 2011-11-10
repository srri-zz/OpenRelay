import os

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class FileBasedStorage(FileSystemStorage):
    """
    Simple wrapper for the stock Django FileSystemStorage class
    """
    def __init__(self, *args, **kwargs):
        super(FileBasedStorage, self).__init__(*args, **kwargs)
        self.location = FILESTORAGE_LOCATION


FILESTORAGE_LOCATION = getattr(settings, 'CONTENT_FILESTORAGE_LOCATION', '/tmp')
STORAGE_BACKEND = getattr(settings, 'CONTENT_STORAGE_BACKEND', FileBasedStorage)
