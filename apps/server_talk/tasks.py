import datetime
import logging

from django.utils.simplejson import dumps

from lock_manager import Lock, LockError
from openrelay_resources.literals import TIMESTAMP_SEPARATOR

from server_talk.exceptions import (HeartbeatError, InventoryHashError,
    SiblingsHashError, SiblingsListError, ResourceListError)
from server_talk.api import RemoteCall
from server_talk.models import LocalNode, Sibling, NetworkResourceVersion, ResourceHolder
from server_talk.literals import NODE_STATUS_DOWN, NODE_STATUS_UP
from server_talk.conf.settings import HEARTBEAT_FAILURE_THRESHOLD

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
            lock = Lock.acquire_lock(u''.join(['heartbeat_check', oldest.uuid]), 20)
        except LockError:
            logging.debug('unable to acquire lock')
        else:
            node = RemoteCall(uuid=oldest.uuid)
            try:
                response = node.heartbeat()
            except HeartbeatError:
                oldest.status = NODE_STATUS_DOWN
                oldest.failure_count += 1
                oldest.last_heartbeat = datetime.datetime.now()
                oldest.save()
                if oldest.failure_count > HEARTBEAT_FAILURE_THRESHOLD:
                    oldest.delete()
            else:
                oldest.last_heartbeat = datetime.datetime.now()
                oldest.cpuload = int(float(response['cpuload']))
                oldest.status = NODE_STATUS_UP
                oldest.failure_count = 0
                oldest.save()
            finally:
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
            lock = Lock.acquire_lock(u''.join(['inventory_hash', oldest.uuid]), 20)
        except LockError:
            logging.debug('unable to acquire lock')
        else:        
            remote_api = RemoteCall(uuid=oldest.uuid)
            try:
                response = remote_api.inventory_hash()
            except InventoryHashError:
                logger.error('got InventoryHashError')
            else:
                if oldest.inventory_hash != response['inventory_hash']:
                    # Delete this holder from all it's resources to catch
                    # later the ones it doesn't have anymore
                    ResourceHolder.objects.filter(node__uuid=oldest.uuid).delete()
                    try:
                        remote_resources = remote_api.resource_list()
                    except ResourceListError:
                        logger.error('got ResourceListError')
                    else:
                        for remote_resource in remote_resources:
                            uuid, timestamp=remote_resource['uuid'].split(TIMESTAMP_SEPARATOR)
                            resource, created = NetworkResourceVersion.objects.get_or_create(
                                uuid=uuid,
                                timestamp=timestamp,
                                defaults={
                                    'metadata': dumps(remote_resource.get('metadata')),
                                    'signature_properties': dumps(remote_resource.get('signature_properties')),
                                }
                            )
                            resource.resourceholder_set.get_or_create(node=oldest)

                        oldest.last_inventory_hash = datetime.datetime.now()
                        oldest.inventory_hash = response['inventory_hash']
                        oldest.save()
                        # Delete network resources that have no holder
                        NetworkResourceVersion.objects.filter(resourceholder=None).delete()
            finally:
                lock.release()

def siblings_hash_check():
    '''
    Find the node with the oldest siblings hash timestamp and query it
    '''
    logging.debug('DEBUG: inventory_hash_check()')
    siblings = Sibling.objects.filter(status=NODE_STATUS_UP).order_by('last_siblings_hash')
    if siblings:
        oldest = siblings[0]
        try:
            lock = Lock.acquire_lock(u''.join(['siblings_hash', oldest.uuid]), 20)
        except LockError:
            logging.debug('unable to acquire lock')
        else:
            remote_api = RemoteCall(uuid=oldest.uuid)
            try:
                response = remote_api.siblings_hash()
            except SiblingsHashError:
                logger.error('got SiblingsHashError')
            else:
                if oldest.siblings_hash != response['siblings_hash']:
                    try:
                        sibling_list = remote_api.siblings_list()
                    except SiblingsListError:
                        logger.error('got SiblingsListError')
                    else:
                        for remote_sibling in sibling_list:
                            # Don't use a precomputed list, to a DB check each time
                            # to minimize posibility of race cond
                            # TODO: add locking
                            try:
                                Sibling.objects.get(uuid=remote_sibling['uuid'])
                            except Sibling.DoesNotExist:
                                # Only add nodes not known
                                if remote_sibling['uuid'] != LocalNode.get().uuid:
                                    # Don't add self
                                    sibling = Sibling()
                                    sibling.uuid=remote_sibling['uuid']
                                    sibling.port=remote_sibling['port']
                                    sibling.ip_address=remote_sibling['ip_address']
                                    sibling.save()

                        oldest.last_siblings_hash = datetime.datetime.now()
                        oldest.siblings_hash = response['siblings_hash']
                        oldest.save()
            finally:
                lock.release()
