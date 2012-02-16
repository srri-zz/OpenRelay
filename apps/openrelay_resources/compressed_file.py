import zipfile

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from django.core.files import File


class NotACompressedFile(Exception):
    pass


class CompressedChild(File):
    def __init__(self, file, name=None):
        if name is None:
            name = getattr(file, 'name', None)
        self.name = name

        try:
            descriptor = file.open()
        except AttributeError:
            # Keep compatibility with other compressed file libraries
            # that return a true file-like object and not an already
            # opened descriptor like zfobj
            descriptor = file

        self.file = StringIO(descriptor.read())
        descriptor.close()


class CompressedFile(object):
    def __init__(self, file_object):
        self.file_object = file_object

    def children(self):
        try:
            # Try for a ZIP file
            zfobj = zipfile.ZipFile(self.file_object)
            filenames = [filename for filename in zfobj.namelist() if not filename.endswith('/')]
            return (CompressedChild(file=zfobj.open(filename)) for filename in filenames)
        except zipfile.BadZipfile:
            raise NotACompressedFile

    def close(self):
        self.file_object.close()
