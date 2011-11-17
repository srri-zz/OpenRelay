# OpenRelay server talk protocol V0.1:

# ping: request a pong from another server and stores the delay in weighted running average for the server
# contacts: requests a list of servers from another server
# inventory: requests a list of resources
# proxy: relays an Http request to another server
# request-resource: request a resource from another server
# my_name_is: request server info (version, api version)
# workaholic: requests the cpu load and resource serving stats of a server (could be merged with [ping])
# report: blacklist a server that has repeatedly tampered with files

import urlparse
import logging
import socket

import requests

from django.utils.simplejson import loads
from django.core.urlresolvers import reverse

from djangorestframework import status

from server_talk.models import LocalNode, Sibling
from server_talk.conf.settings import PORT
from server_talk.exceptions import AnnounceClientError, NoSuchNode, \
    HeartbeatError, InventoryHashError

logger = logging.getLogger(__name__)


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

    def get_service_url(self, service_name):
        return urlparse.urlunparse(['http', self.get_full_ip_address(), reverse(service_name), '', '', ''])
        
    def announce(self):
        '''
        Announce the local node to another OpenRelay node
        '''
        local_node_info = {
            'ip_address': socket.gethostbyname(socket.gethostname()),
            'port': PORT,
            'uuid': LocalNode.get().uuid,
        }
        full_ip_address = self.get_full_ip_address()
        url = self.get_service_url('service-announce')
        try:
            response = requests.post(url, data=local_node_info)
        except requests.ConnectionError:
            logger.error('unable to connect to url: %s' % url)
            raise AnnounceClientError('Unable to join network')

        if response.status_code == status.OK:
            node_answer = loads(response.content)
            if node_answer['uuid'] == LocalNode.get().uuid:
                logger.error('announce service on node with uuid: %s and url: %s, responded the same UUID as the local server' % (node_answer['uuid'], full_ip_address))
                raise AnnounceClientError('Remote and local nodes identity conflict')
            else:
                sibling_data = {'ip_address':  node_answer['ip_address'], 'port': node_answer['port']}
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
            response = requests.get(url, data={'uuid': LocalNode.get().uuid})
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
            response = requests.get(url, data={'uuid': LocalNode.get().uuid})
            logger.debug('received inventory_hash from url: %s' % url)
            return loads(response.content)
        except requests.ConnectionError:
            logger.error('unable to connect to url: %s' % url)
            raise InventoryHashError('Unable to query node')            
