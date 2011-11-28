from django_gpg import GPG

from core.conf.settings import KEYSERVERS

gpg = GPG(keyservers=KEYSERVERS)

