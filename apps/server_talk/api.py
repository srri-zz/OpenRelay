import urlparse
import logging

import requests

from django.utils.simplejson import loads, dumps
from django.core.urlresolvers import reverse
from django.core.serializers.json import DjangoJSONEncoder

#from djangorestframework import status
from rest_framework import status

from openrelay_resources.models import Resource, Version
from openrelay_resources.exceptions import ORInvalidResourceFile
from core.runtime import gpg
from django_gpg import (KeyFetchingError, GPGVerificationError,
    GPGDecryptionError)

from server_talk.models import LocalNode, Sibling, NetworkResourceVersion
from server_talk.conf.settings import (PORT, IPADDRESS, KEY_PASSPHRASE, TIMEOUT)
from server_talk.exceptions import (AnnounceClientError, NoSuchNode,
    HeartbeatError, InventoryHashError, ResourceListError,
    NetworkResourceNotFound, NetworkResourceDownloadError, SiblingsHashError,
    SiblingsListError, NodeDataPackageError)
from server_talk.literals import NODE_STATUS_UP

logger = logging.getLogger(__name__)


def decrypt_request_data(signed_data):
    try:
        result = gpg.verify(signed_data, retry=True)
        result = gpg.decrypt(signed_data)
    except (KeyFetchingError, GPGVerificationError):
        logger.error('got verify exception')
        raise NodeDataPackageError('package signature failure')
    except GPGDecryptionError:
        logger.error('got GPGDecryptionError')
        raise NodeDataPackageError('package decryption failure')
    else:
        try:
            return result.pubkey_fingerprint, loads(result.data)
        except ValueError:
            logger.error('non JSON data')
            logger.debug('got: %s' % result.data)
            return result.pubkey_fingerprint, {}


def prepare_package(package):
    return {'signed_data': gpg.sign(dumps(package, cls=DjangoJSONEncoder), key=LocalNode().public_key, passphrase=KEY_PASSPHRASE).data}


class NetworkCall(object):
    def find_resource(self, uuid):
        try:
            network_resource_version = NetworkResourceVersion.objects.get(uuid=uuid)
            # Get the holder with the lowest CPU load and that are alive
            resource_holder = network_resource_version.resourceholder_set.filter(node__status=NODE_STATUS_UP).order_by('-node__cpuload')[0].node
            node = RemoteCall(uuid=resource_holder.uuid)
            resource_raw_data = node.download_version(uuid)
            remote_resource = Version.create_from_raw(resource_raw_data)
            Resource.storage_culling()
            return remote_resource

        except (NetworkResourceVersion.DoesNotExist, IndexError, ORInvalidResourceFile, NetworkResourceDownloadError), msg:
            raise NetworkResourceNotFound(msg)

    def publish_key(self, key):
        # For now publishes key to http://peer.to keyserver
        response = requests.post(u'http://peer.to:11371/pks/add', data={'keytext': key.data}, timeout=TIMEOUT)


class RemoteCall(object):
    def __init__(self, *args, **kwargs):
        self.ip_address = kwargs.pop('ip_address', '')
        self.port = kwargs.pop('port', '')
        self.uuid = kwargs.pop('uuid', None)

        if not self.ip_address:
            try:
                sibling = Sibling.objects.get(uuid=self.uuid)
                self.ip_address = sibling.ip_address
                self.port = sibling.port
            except Sibling.DoesNotExist:
                raise NoSuchNode('Node: %s, does not exists' % uuid)


    def get_full_ip_address(self):
        return u'%s%s' % (self.ip_address, u':%s' % self.port if self.port else '')

    def get_service_url(self, service_name, *args, **kwargs):
        return urlparse.urlunparse(['http', self.get_full_ip_address(), reverse(service_name, *args, **kwargs), '', '', ''])

    def get_id_package(self):
        return prepare_package({
            'ip_address': IPADDRESS,
            'port': PORT,
        })

    def announce(self):
        '''
        Announce the local node to another OpenRelay node
        '''
        full_ip_address = self.get_full_ip_address()
        url = self.get_service_url('service-announce')
        try:
            signed_data = self.get_id_package()
            logger.debug('signed data: %s' % signed_data)
            response = requests.post(url, data=signed_data, timeout=TIMEOUT)
        except (requests.ConnectionError, requests.Timeout):
            logger.error('unable to connect to url: %s' % url)
            raise AnnounceClientError('Unable to join network')
        else:
            if response.status_code == status.OK:
                try:
                    result = loads(response.content)
                    fingerprint, node_answer = decrypt_request_data(result['signed_data'])
                except NodeDataPackageError:
                    raise AnnounceClientError('id package signature failure')
                except ValueError:
                    raise AnnounceClientError('non JSON response')
                else:
                    if fingerprint == LocalNode().uuid:
                        logger.error('announce service on node with uuid: %s and url: %s, responded the same UUID as the local server' % (node_answer['uuid'], full_ip_address))
                        raise AnnounceClientError('Remote and local nodes identity conflict')
                    else:
                        sibling_data = {
                            'ip_address':  node_answer['ip_address'],
                            'port': node_answer['port'],
                        }
                        sibling, created = Sibling.objects.get_or_create(uuid=fingerprint, defaults=sibling_data)
                        if not created:
                            sibling.ip_address = sibling_data['ip_address']
                            sibling.port = sibling_data['port']
                            sibling.save()
            else:
                logger.error('announce service on remote node responded with a non OK code')
                raise AnnounceClientError('Unable to join network')

    def heartbeat(self):
        '''
        Check a host's availability and cpu load
        '''
        url = self.get_service_url('service-heartbeat')
        try:
            logger.debug('calling heartbeat service on url: %s' % url)
            request = requests.post(url, data=self.get_id_package(), timeout=TIMEOUT)
            logger.debug('received heartbeat from url: %s' % url)
        except (requests.ConnectionError, requests.Timeout):
            logger.error('unable to connect to url: %s' % url)
            raise HeartbeatError('Unable to query node')
        else:
            try:
                response = loads(request.content)
                return decrypt_request_data(response['signed_data'])
            except ValueError:
                raise HeartbeatError('non JSON data')
            except NodeDataPackageError, exc:
                raise HeartbeatError(exc)

    def inventory_hash(self):
        '''
        Ask for a node's hash of it's inventories
        '''
        url = self.get_service_url('service-inventory_hash')
        try:
            logger.debug('calling inventory_hash service on url: %s' % url)
            request = requests.post(url, data=self.get_id_package(), timeout=TIMEOUT)
            logger.debug('received inventory_hash from url: %s' % url)
        except (requests.ConnectionError, requests.Timeout):
            logger.error('unable to connect to url: %s' % url)
            raise InventoryHashError('Unable to query node')
        else:
            try:
                response = loads(request.content)
                return decrypt_request_data(response['signed_data'])
            except ValueError:
                raise InventoryHashError('non JSON data')
            except NodeDataPackageError, exc:
                raise InventoryHashError(exc)

    def siblings_hash(self):
        '''
        Ask for a node's hash of it's known node list
        '''
        url = self.get_service_url('service-siblings_hash')
        try:
            logger.debug('calling siblings_hash service on url: %s' % url)
            request = requests.post(url, data=self.get_id_package(), timeout=TIMEOUT)
            logger.debug('received siblings_hash from url: %s' % url)
        except (requests.ConnectionError, requests.Timeout):
            logger.error('unable to connect to url: %s' % url)
            raise SiblingsHashError('Unable to query node')
        else:
            try:
                response = loads(request.content)
                return decrypt_request_data(response['signed_data'])
            except ValueError:
                raise SiblingsHashError('non JSON data')
            except NodeDataPackageError, exc:
                raise SiblingsHashError(exc)

    def resource_list(self):
        '''
        Retrieve a node's resource list
        '''
        url = self.get_service_url('version-root')
        try:
            logger.debug('calling resource_list service on url: %s' % url)
            request = requests.post(url, data=self.get_id_package(), timeout=TIMEOUT)
            logger.debug('received resource_list from url: %s' % url)
        except (requests.ConnectionError, requests.Timeout):
            logger.error('unable to connect to url: %s' % url)
            raise ResourceListError('Unable to query node')
        else:
            try:
                response = loads(request.content)
                return decrypt_request_data(response['signed_data'])
            except ValueError:
                raise ResourceListError('non JSON data')
            except NodeDataPackageError, exc:
                raise ResourceListError(exc)

    def siblings_list(self):
        '''
        Retrieve a node's resource list
        '''
        url = self.get_service_url('sibling-root')
        try:
            logger.debug('calling sibling-root service on url: %s' % url)
            request = requests.post(url, data=self.get_id_package(), timeout=TIMEOUT)
            logger.debug('received sibling-root from url: %s' % url)
        except (requests.ConnectionError, requests.Timeout):
            logger.error('unable to connect to url: %s' % url)
            raise SiblingListError('Unable to query node')
        else:
            try:
                response = loads(request.content)
                return decrypt_request_data(response['signed_data'])
            except ValueError:
                raise SiblingListError('non JSON data')
            except NodeDataPackageError, exc:
                raise SiblingListError(exc)

    def download_version(self, uuid):
        '''
        Download a resource version from a remote node
        '''
        url = self.get_service_url('version-download', args=[uuid])
        try:
            logger.debug('calling version download on url: %s' % url)
            request = requests.post(url, data=self.get_id_package(), timeout=TIMEOUT)
            logger.debug('received download from url: %s' % url)
        except (requests.ConnectionError, requests.Timeout):
            logger.error('unable to connect to url: %s' % url)
            raise NetworkResourceDownloadError('Unable to query node')
        else:
            try:
                response = loads(request.content)
                return decrypt_request_data(response['signed_data'])
            except ValueError:
                raise NetworkResourceDownloadError('non JSON data')
            except NodeDataPackageError, exc:
                raise NetworkResourceDownloadError(exc)
