import datetime
import logging
import uuid

from django.db.models.signals import post_syncdb
from django.dispatch import receiver

from lock_manager.models import Lock
from lock_manager.exceptions import LockError
from core.runtime import scheduler

#TODO: rename Resource to NetworkResource
from server_talk.models import LocalNode, Sibling, NetworkResource, ResourceHolder
from server_talk import models as server_talk_model
from server_talk.exceptions import HeartbeatError, InventoryHashError
from server_talk.api import RemoteCall
from server_talk.conf.settings import HEARTBEAT_QUERY_INTERVAL, \
INVENTORY_QUERY_INTERVAL


logger = logging.getLogger(__name__)


@receiver(post_syncdb, dispatch_uid='create_identify', sender=server_talk_model)
def create_identify(sender, **kwargs):
    print 'Creating local node identity ...'
    info, created = LocalNode.objects.get_or_create(lock_id='1', defaults={'uuid': unicode(uuid.uuid4())})
    if not created:
        print 'Existing identify not modified.'


#@scheduler.interval_schedule(seconds=HEARTBEAT_QUERY_INTERVAL)
def heartbeat_check():
    '''
    Find the node with the oldest hearbeat timestamp and query it
    '''
    logging.debug('DEBUG: heartbeat_check()')
    siblings = Sibling.objects.all().order_by('last_heartbeat')
    if siblings:
        oldest = siblings[0]
        try:
            lock = Lock.objects.acquire_lock(u''.join(['heartbeat_check', oldest.uuid]), 20)
            node = RemoteCall(uuid=oldest.uuid)
            oldest.last_heartbeat = datetime.datetime.now()
            response = node.heartbeat()
            oldest.cpuload = int(float(response['cpuload']))
            oldest.save()
            lock.release()
        except LockError:
            pass
        except HeartbeatError:
            lock.release()


#@scheduler.interval_schedule(seconds=INVENTORY_QUERY_INTERVAL)
def inventory_hash_check():
    '''
    Find the node with the oldest inventory timestamp and query it
    '''
    logging.debug('DEBUG: inventory_hash_check()')
    siblings = Sibling.objects.all().order_by('last_inventory_hash')
    if siblings:
        oldest = siblings[0]
        try:
            lock = Lock.objects.acquire_lock(u''.join(['inventory_hash', oldest.uuid]), 20)
            oldest.last_inventory_hash = datetime.datetime.now()
            remote_api = RemoteCall(uuid=oldest.uuid)
            response = remote_api.inventory_hash()
            if oldest.inventory_hash != response['inventory_hash']:
                # Delete this holder from all it's resources to catch
                # later the ones it doesn't have anymore
                ResourceHolder.objects.filter(node__uuid=oldest.uuid).delete()
                for resource_item in remote_api.resource_list():
                    resource, created = NetworkResource.objects.get_or_create(uuid=resource_item['uuid'], time_stamp=resource_item['time_stamp'])
                    resource.resourceholder_set.get_or_create(node=oldest)
                
            oldest.inventory_hash = response['inventory_hash']
            oldest.save()
            # Delete network resources that have no holder
            NetworkResource.objects.filter(resourceholder=None).delete()
            lock.release()
        except LockError:
            pass
        except InventoryHashError:
            lock.release()
