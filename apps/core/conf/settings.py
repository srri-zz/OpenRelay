from django.conf import settings

KEYSERVERS = getattr(settings, 'CORE_KEYSERVERS', [
    'http://peer.to:11371',
])
