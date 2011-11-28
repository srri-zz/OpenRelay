from django.conf import settings

KEYSERVERS = getattr(settings, 'CORE_KEYSERVERS', [
    'peer.to',
])
