import datetime
import logging
import uuid

from django.db.models.signals import post_syncdb
from django.dispatch import receiver

from lock_manager.models import Lock
from lock_manager.exceptions import LockError
from core.runtime import scheduler

from server_talk.models import LocalNode, Sibling
from server_talk import models as server_talk_model
from server_talk.exceptions import HeartbeatError
from server_talk.api import RemoteCall
from server_talk.conf.settings import HEARTBEAT_QUERY_INTERVAL

logger = logging.getLogger(__name__)


@receiver(post_syncdb, dispatch_uid='create_identify', sender=server_talk_model)
def create_identify(sender, **kwargs):
    print 'Creating local node identity ...'
    info, created = LocalNode.objects.get_or_create(lock_id='1', defaults={'uuid': unicode(uuid.uuid4())})
    if not created:
        print 'Existing identify not modified.'


@scheduler.interval_schedule(seconds=HEARTBEAT_QUERY_INTERVAL)
def heartbeat_check():
    '''
    Find the node with the oldest hearbeat timestamp and query it
    '''
    logging.debug('DEBUG: heartbeat_check()')
    siblings = Sibling.objects.all().order_by('last_heartbeat')
    if siblings:
        oldest = siblings[0]
        try:
            lock = Lock.objects.acquire_lock(oldest.uuid, 10)
            node = RemoteCall(uuid=oldest.uuid)
            oldest.last_heartbeat = datetime.datetime.now()
            response = node.heartbeat()
            oldest.cpuload = int(float(response['cpuload']))
            oldest.save()
            Lock.objects.release_lock(oldest.uuid)
        except LockError:
            pass
        except HeartbeatError:
            Lock.objects.release_lock(oldest.uuid)

