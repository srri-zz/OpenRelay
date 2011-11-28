from django_gpg.api import GPG, Key
from django_gpg.exceptions import GPGVerificationError, \
    GPGDecryptionError, GPGSigningError, KeyDeleteError, \
    KeyGenerationError, KeyFetchingError, KeyDoesNotExist
from django_gpg.tasks import background_key_generator, BACKGROUND_KEY_GENERATOR_INTERVAL

from scheduler import register_interval_job

register_interval_job('background_key_generator', background_key_generator, seconds=BACKGROUND_KEY_GENERATOR_INTERVAL)

