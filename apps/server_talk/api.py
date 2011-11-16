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

from django.utils.simplejson import dumps, loads
from django.core.urlresolvers import reverse

from djangorestframework import status

from server_talk.models import LocalNode, Sibling
from server_talk.conf.settings import PORT
from server_talk.exceptions import AnnounceClientError

logger = logging.getLogger(__name__)


class RemoteCall(object):
    def __init__(self, *args, **kwargs):
        self.ip_address = kwargs.pop('ip_address', '')
        self.port = kwargs .pop('port', '')
        self.uuid = kwargs.pop('uuid', None)
    
    def announce(self):
        '''
        Announce ourselves to another OpenRelay node
        '''
        local_node_info = {
            'ip_address': socket.gethostbyname(socket.gethostname()),
            'port': PORT,
            'uuid': LocalNode.get().uuid,
        }
        full_ip_address = u'%s%s' % (self.ip_address, u':%s' % self.port if self.port else '')
        url = urlparse.urlunparse(['http', full_ip_address, reverse('service-announce'), '', '', ''])
        
        try:
            response = requests.post(url, data=local_node_info)
        except requests.ConnectionError:
            logger.error('ERROR: unable to connect to url: %s' % url)
            raise AnnounceClientError('Unable to join network')

        if response.status_code == status.OK:
            node_answer = loads(response.content)
            if node_answer['uuid'] == LocalNode.get().uuid:
                logger.error('ERROR: announce service on node with uuid: %s and url: %s, responded the same UUID as the local server' % (node_answer['uuid'], full_ip_address))
                raise AnnounceClientError('Remote and local nodes identity conflict')
            else:
                sibling_data = {'ip_address':  node_answer['ip_address'], 'port': node_answer['port']}
                sibling, created = Sibling.objects.get_or_create(uuid=node_answer['uuid'], defaults=sibling_data)
                if not created:
                    sibling.ip_address = sibling_data['ip_address']
                    sibling.port = sibling_data['port']
                    sibling.save()                
        else:
            logger.error('ERROR: announce service on remote node responded with a non OK code')
            raise AnnounceClientError('Unable to join network')
