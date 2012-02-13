from django_gpg import GPG

from core.conf.settings import KEYSERVERS, GPG_HOME

gpg = GPG(keyservers=KEYSERVERS, home=GPG_HOME)

