"""The root view for OpenRelay API"""
import logging
import socket

from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib import messages
from django.core.urlresolvers import reverse

from djangorestframework.mixins import InstanceMixin, ReadModelMixin
from djangorestframework.views import View, ModelView
from djangorestframework import status
from djangorestframework.response import Response

from server_talk.models import LocalNode, Sibling
from server_talk.forms import JoinForm
from server_talk.api import RemoteCall
from server_talk.conf.settings import PORT
from server_talk.exceptions import AnnounceClientError
from server_talk.utils import CPUsage

logger = logging.getLogger(__name__)


class OpenRelayAPI(View):
    """This is the REST API for OpenRelay (https://github.com/Captainkrtek/OpenRelay).

    All the API calls allow anonymous access, and can be navigated either through the browser or from the command line...

        bash: curl -X GET http://127.0.0.1:8000/api/                           # (Use default renderer)
        bash: curl -X GET http://127.0.0.1:8000/api/ -H 'Accept: text/plain'   # (Use plaintext documentation renderer)

    """

    def get(self, request):
        return [
            {'name': 'Resources', 'url': reverse('resource-root')},
            {'name': 'Services', 'url': reverse('service-root')}
        ]


class ReadOnlyInstanceModelView(InstanceMixin, ReadModelMixin, ModelView):
    """A view which provides default operations for read only against a model instance."""
    _suffix = 'Instance'


class Services(View):
    def get(self, request):
        return [
            {'name': 'Announce', 'url': reverse('service-announce')},
            {'name': 'Heartbeat', 'url': reverse('service-heartbeat')},
        ]


class Announce(View):
    def post(self, request):
        uuid = request.POST.get('uuid')
        ip_address = request.POST.get('ip_address')
        port = request.POST.get('port')
        logger.info('received announce call from: %s @ %s' % (uuid, request.META['REMOTE_ADDR']))
        if uuid and ip_address and port:
            sibling_data = {'ip_address': ip_address, 'port': port}
            sibling, created = Sibling.objects.get_or_create(uuid=uuid, defaults=sibling_data)
            if not created:
                sibling.ip_address = sibling_data['ip_address']
                sibling.port = sibling_data['port']
                sibling.save()
            local_node_info = {
                'ip_address': socket.gethostbyname(socket.gethostname()),
                'port': PORT,
                'uuid': LocalNode.get().uuid,
            }
            return local_node_info
        else:
            return Response(status.PARTIAL_CONTENT)


class Heartbeat(View):
    def get(self, request):
        uuid = request.POST.get('uuid')
        logger.info('received heartbeat call from: %s @ %s' % (uuid, request.META['REMOTE_ADDR']))
        return {'cpuload': CPUsage()}


def join(request):
    if request.method == 'POST':
        form = JoinForm(request.POST)
        if form.is_valid():
            try:
                entry_point = RemoteCall(
                    ip_address=form.cleaned_data['ip_address'],
                    port=form.cleaned_data['port']
                )
                entry_point.announce()
                messages.success(request, _(u'Join request sent'))
                return HttpResponseRedirect(reverse('home_view'))
            except AnnounceClientError:
                messages.error(request, _(u'Unable to join network'))
                return HttpResponseRedirect(reverse('join'))
    else:
        form = JoinForm()

    return render_to_response('generic_form.html', {
        'form': form,
        'title': _(u'Join the OpenRelay network via a remote node'),
    }, context_instance=RequestContext(request))


def node_list(request):
    return render_to_response('node_list.html', {
        'object_list': Sibling.objects.all(),
        'title': _(u'Network node list'),
    }, context_instance=RequestContext(request))


def node_info(request):
    return render_to_response('node_list.html', {
        'object_list': [LocalNode.get()],
        'title': _(u'Local node information'),
    }, context_instance=RequestContext(request))
