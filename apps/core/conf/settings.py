from django.conf import settings

KEYSERVERS = getattr(settings, 'CORE_KEYSERVERS', [
    'ldap://keyserver.pgp.com',
    'hkp://keyserver.ubuntu.com:11371',
    'hkp://pool.sks-keyservers.net'   
])
