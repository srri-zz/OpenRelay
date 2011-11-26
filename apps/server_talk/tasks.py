import datetime
import logging

from lock_manager.models import Lock
from lock_manager.exceptions import LockError
from openrelay_resources.literals import TIMESTAMP_SEPARATOR

from server_talk.exceptions import HeartbeatError, InventoryHashError
from server_talk.api import RemoteCall
from server_talk.models import LocalNode, Sibling, NetworkResourceVersion, ResourceHolder
from server_talk.literals import NODE_STATUS_DOWN, NODE_STATUS_UP

logger = logging.getLogger(__name__)


def heartbeat_check():
    '''
    Find the node with the oldest hearbeat timestamp and query it
    '''
    logging.debug('DEBUG: heartbeat_check()')
    siblings = Sibling.objects.filter().order_by('last_heartbeat')
    if siblings:
        oldest = siblings[0]
        try:
            lock = Lock.objects.acquire_lock(u''.join(['heartbeat_check', oldest.uuid]), 20)
            node = RemoteCall(uuid=oldest.uuid)
            oldest.last_heartbeat = datetime.datetime.now()
            response = node.heartbeat()
            oldest.cpuload = int(float(response['cpuload']))
            oldest.status = NODE_STATUS_UP
            oldest.save()
            lock.release()
        except LockError:
            pass
        except HeartbeatError:
            oldest.status = NODE_STATUS_DOWN
            oldest.save()
            lock.release()


# TODO: move DB logic to api.py
def inventory_hash_check():
    '''
    Find the node with the oldest inventory timestamp and query it
    '''
    logging.debug('DEBUG: inventory_hash_check()')
    siblings = Sibling.objects.filter(status=NODE_STATUS_UP).order_by('last_inventory_hash')
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
                    uuid, timestamp=resource_item['uuid'].split(TIMESTAMP_SEPARATOR)
                    resource, created = NetworkResourceVersion.objects.get_or_create(
                        uuid=uuid,
                        timestamp=timestamp,
                        defaults={
                            'name': resource_item.get('name'),
                            'label': resource_item.get('label'),
                            'description': resource_item.get('description'),
                        }
                    )
                    resource.resourceholder_set.get_or_create(node=oldest)
                
            oldest.inventory_hash = response['inventory_hash']
            oldest.save()
            # Delete network resources that have no holder
            NetworkResourceVersion.objects.filter(resourceholder=None).delete()
            lock.release()
        except LockError:
            pass
        except InventoryHashError:
            lock.release()
