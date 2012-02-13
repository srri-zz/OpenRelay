import os

from django.conf import settings

KEYSERVERS = getattr(settings, 'CORE_KEYSERVERS', [
    'peer.to',
])

GPG_HOME = getattr(settings, 'CORE_GPG_HOME', os.path.join(settings.PROJECT_ROOT, u'gpg_home'))
