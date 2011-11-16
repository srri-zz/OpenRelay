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


FILESTORAGE_LOCATION = getattr(settings, 'RESOURCES_FILESTORAGE_LOCATION', os.path.join(settings.PROJECT_ROOT, 'resource_storage'))
STORAGE_BACKEND = getattr(settings, 'RESOURCES_STORAGE_BACKEND', FileBasedStorage)
