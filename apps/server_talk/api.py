# OpenRelay server talk protocol V0.1:

# ping: request a pong from another server and stores the delay in weighted running average for the server
# contacts: requests a list of servers from another server
# inventory: requests a list of resources
# proxy: relays an Http request to another server
# request-resource: request a resource from another server
# my_name_is: request server info (version, api version)
# workaholic: requests the cpu load and resource serving stats of a server (could be merged with [ping])
# report: blacklist a server that has repeatedly tampered with files (from authoritative nodes only)
# unblacklist

import urlparse
import logging

import requests

from django.utils.simplejson import loads
from django.core.urlresolvers import reverse

from djangorestframework import status

from openrelay_resources.models import Resource, Version
from openrelay_resources.exceptions import ORInvalidResourceFile

from server_talk.models import LocalNode, Sibling, NetworkResourceVersion
from server_talk.conf.settings import PORT, IPADDRESS
from server_talk.exceptions import (AnnounceClientError, NoSuchNode,
    HeartbeatError, InventoryHashError, ResourceListError,
    NetworkResourceNotFound, NetworkResourceDownloadError)
from server_talk.literals import NODE_STATUS_UP

logger = logging.getLogger(__name__)


class NetworkCall(object):
    def find_resource(self, uuid):
        try:
            network_resource_version = NetworkResourceVersion.objects.get(uuid=uuid)
            # Get the holder with the lowest CPU load and that are alive
            resource_holder = network_resource_version.resourceholder_set.filter(node__status=NODE_STATUS_UP).order_by('-node__cpuload')[0].node
            node = RemoteCall(uuid=resource_holder.uuid)
            resource_raw_data = node.download_version(uuid)
            remote_resource = Version.create_from_raw(resource_raw_data)
            return remote_resource

        except (NetworkResourceVersion.DoesNotExist, IndexError, ORInvalidResourceFile, NetworkResourceDownloadError), msg:
            raise NetworkResourceNotFound(msg)
            
    def publish_key(self, key):
        # For now publishes key to http://peer.to keyserver
        response = requests.post(u'http://peer.to:11371/pks/add', data={'keytext': key.data})


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
        local_node = LocalNode.get()
        return {
            'ip_address': IPADDRESS,
            'port': PORT,
            'uuid': local_node.uuid,
        }
        
    def announce(self):
        '''
        Announce the local node to another OpenRelay node
        '''
        full_ip_address = self.get_full_ip_address()
        url = self.get_service_url('service-announce')
        try:
            response = requests.post(url, data=self.get_id_package())
        except requests.ConnectionError:
            logger.error('unable to connect to url: %s' % url)
            raise AnnounceClientError('Unable to join network')

        if response.status_code == status.OK:
            node_answer = loads(response.content)
            if node_answer['uuid'] == LocalNode.get().uuid:
                logger.error('announce service on node with uuid: %s and url: %s, responded the same UUID as the local server' % (node_answer['uuid'], full_ip_address))
                raise AnnounceClientError('Remote and local nodes identity conflict')
            else:
                sibling_data = {
                    'ip_address':  node_answer['ip_address'],
                    'port': node_answer['port'],
                    'name': node_answer['name'],
                    'email': node_answer['email'],
                    'comment': node_answer['comment'],
                }
                sibling, created = Sibling.objects.get_or_create(uuid=node_answer['uuid'], defaults=sibling_data)
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
            response = requests.post(url, data=self.get_id_package())
            logger.debug('received heartbeat from url: %s' % url)
            return loads(response.content)
        except requests.ConnectionError:
            logger.error('unable to connect to url: %s' % url)
            raise HeartbeatError('Unable to query node')
            
    def inventory_hash(self):
        '''
        Ask for a node's hash of it's inventories
        '''
        url = self.get_service_url('service-inventory_hash')
        try:
            logger.debug('calling inventory_hash service on url: %s' % url)
            response = requests.post(url, data=self.get_id_package())
            logger.debug('received inventory_hash from url: %s' % url)
            return loads(response.content)
        except requests.ConnectionError:
            logger.error('unable to connect to url: %s' % url)
            raise InventoryHashError('Unable to query node')

    def resource_list(self):
        '''
        Retrieve a node's resource list
        '''
        url = self.get_service_url('version-root')
        try:
            logger.debug('calling resource_list service on url: %s' % url)
            response = requests.post(url, data=self.get_id_package())
            logger.debug('received resource_list from url: %s' % url)
            return loads(response.content)
        except requests.ConnectionError:
            logger.error('unable to connect to url: %s' % url)
            raise ResourceListError('Unable to query node')
            
    def heartbeat(self):
        '''
        Check a host's availability and cpu load
        '''
        url = self.get_service_url('service-heartbeat')
        try:
            logger.debug('calling heartbeat service on url: %s' % url)
            response = requests.post(url, data=self.get_id_package())
            logger.debug('received heartbeat from url: %s' % url)
            return loads(response.content)
        except requests.ConnectionError:
            logger.error('unable to connect to url: %s' % url)
            raise HeartbeatError('Unable to query node')          
            
    def download_version(self, uuid):
        '''
        Download a resource version from a remote node
        '''
        url = self.get_service_url('version-download', args=[uuid])
        try:
            logger.debug('calling version download on url: %s' % url)
            response = requests.post(url, data=self.get_id_package())
            logger.debug('received download from url: %s' % url)
            return response.content
        except requests.ConnectionError:
            logger.error('unable to connect to url: %s' % url)
            raise NetworkResourceDownloadError('Unable to query node')
