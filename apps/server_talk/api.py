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

from django.test.client import Client
from django.utils.simplejson import dumps, loads
from django.core.urlresolvers import reverse

from djangorestframework import status

#HTTP_200_OK = 200
#HTTP_201_CREATED = 201
#HTTP_202_ACCEPTED = 202
#HTTP_203_NON_AUTHORITATIVE_INFORMATION = 203
#HTTP_204_NO_CONTENT = 204
#HTTP_205_RESET_CONTENT = 205
#HTTP_206_PARTIAL_CONTENT = 206

class RemoteCall(object):
    
    def __init__(self, url=None, uuid=None):
        self.url=url
        self.uuid=uuid
    
    
    def announce(self):
        '''
        Announce ourselves to another OpenRelay node
        '''
        c = Client()
        response = c.post(urlparse.urljoin(self.url, reverse('service-announce')), {'name': 'fred', 'passwd': 'secret'})
        if response.status_code == status.HTTP_200_OK:
            print loads(response.content)
        else:
            print 'error'
