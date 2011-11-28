import logging 
from pickle import loads

from django.contrib import messages
from django.utils.translation import ugettext_lazy as _

from queue_manager import Queue, QueuePushError

from django_gpg.exceptions import KeyGenerationError

logger = logging.getLogger(__name__)

BACKGROUND_KEY_GENERATOR_INTERVAL = 10


def background_key_generator():
    queue = Queue(queue_name='gpg_key_gen')
    kwargs = queue.pull()
    if kwargs:
        msg_queue = Queue(queue_name='gpg_msg_queue')
        try:
            gpg = loads(str(kwargs.pop('gpg')))
            key = gpg.create_key(**kwargs)
            msg_queue.push(
                data={
                    'tag': messages.SUCCESS,
                    'message': _(u'Key pair: %s, created successfully.') % key.fingerprint
                }
            )
        except Exception, err_msg:
            msg_queue.push(
                data={
                    'tag': messages.ERROR,
                    'message': _(u'Key creation error; %s') % err_msg
                }
            )
        
