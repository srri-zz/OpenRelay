from gpg import GPG
from content import ContentCache, ContentStorage

# Initialize a project wide instance of GPG
gpg = GPG()
content_cache = ContentCache('/tmp')
content_storage = ContentStorage('/tmp', content_cache)
