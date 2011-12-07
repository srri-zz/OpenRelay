"""The root view for OpenRelay API"""
import logging
import hashlib

from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib import messages
from django.core.urlresolvers import reverse

from djangorestframework.mixins import InstanceMixin, ReadModelMixin
from djangorestframework.views import View, ModelView
from djangorestframework import status
from djangorestframework.response import Response

from openrelay_resources.models import Resource, Version
from openrelay_resources.literals import TIMESTAMP_SEPARATOR

from server_talk.models import LocalNode, Sibling, NetworkResourceVersion
from server_talk.forms import JoinForm
from server_talk.api import RemoteCall
from server_talk.conf.settings import PORT, IPADDRESS
from server_talk.exceptions import AnnounceClientError
from server_talk.utils import CPUsage

logger = logging.getLogger(__name__)
HASH_FUNCTION = lambda x: hashlib.sha256(x).hexdigest()


def _get_object_or_404(model, *args, **kwargs):
    '''
    Custom get_object_or_404 as the Django one call .get() method on a
    QuerySet thus ignoring a custom manager's .get() method
    '''
    try:
        return model.objects.get(*args, **kwargs)
    except model.DoesNotExist:
        raise Http404('No %s matches the given query.' % model._meta.object_name)


# API views
class OpenRelayAPI(View):
    """
    This is the REST API for OpenRelay (https://github.com/Captainkrtek/OpenRelay).
    """

    def get(self, request):
        return [
            {'name': 'Resources', 'url': reverse('resource_file-root')},
            {'name': 'Versions', 'url': reverse('version-root')},
            {'name': 'Announce', 'url': reverse('service-announce')},
            {'name': 'Heartbeat', 'url': reverse('service-heartbeat')},
            {'name': 'Inventory hash', 'url': reverse('service-inventory_hash')},
        ]


class ResourceFileRoot(View):
    def post(self, request):
        return [
            {
                'uuid': resource.uuid,
                'url': reverse('resource_file', args=[resource.uuid]),
            }
            for resource in Resource.objects.all()
        ]


class ResourceFileObject(View):
    def post(self, request, uuid):
        resource = get_object_or_404(Resource, uuid=uuid)
        return {
            'uuid': resource.uuid,
            'name': resource.name,
            'label': resource.label,
            'description': resource.description,
            'metadata': resource.metadata,
            'versions': [
                {
                    'timestamp': version.timestamp,
                    'url': reverse('version', args=[version.full_uuid]),
                }
                for version in resource.version_set.all()
            ],
            'download': reverse('version-download', args=[resource.uuid]),
            'serve': reverse('version-serve', args=[resource.uuid]),
            'latest_version': resource.latest_version().full_uuid,
        }


class VersionRoot(View):
    def post(self, request):
        return [
            {
                'uuid': version.full_uuid,
                'url': reverse('version', args=[version.full_uuid]),
                'name': version.name,
                'label': version.label,
                'description': version.description,
                'metadata': version.metadata,
                'signature_properties': version.signature_properties,
            }
            for version in Version.objects.all()
        ]


class VersionObject(View):
    def post(self, request, uuid):
        version = Resource.objects.get(uuid=uuid)
        return {
            'uuid': version.full_uuid,
            'name': version.name,
            'label': version.label,
            'description': version.description,
            'metadata': version.metadata,
            'exists': version.exists,
            'is_valid': version.is_valid,
            'signature_status': version.signature_status,
            'mimetype': version.mimetype[0],
            'encoding': version.mimetype[1],
            'username': version.username,
            'signature_id': version.signature_id,
            'raw_timestamp': version.raw_timestamp,
            'timestamp': version.timestamp,
            'fingerprint': version.fingerprint,
            'key_id': version.key_id,
            'download': reverse('version-download', args=[version.full_uuid]),
            'serve': reverse('version-serve', args=[version.full_uuid]),
            'signature_properties': version.signature_properties,
            'size': version.size,
        }


class ResourceDownload(View):
    def post(self, request, uuid):
        #logger.info('received resource download call from node: %s @ %s' % (node_uuid, request.META['REMOTE_ADDR']))
        try:
            resource = Resource.objects.get(uuid=uuid)
        except Resource.DoesNotExist:
            raise Http404('No %s matches the given query.' % Resource._meta.object_name)

        return HttpResponse(resource.download())


class ResourceServe(View):
    def post(self, request, uuid):
        #logger.info('received resource serve call from node: %s @ %s' % (node_uuid, request.META['REMOTE_ADDR']))
        try:
            resource = Resource.objects.get(uuid=uuid)
        except Resource.DoesNotExist:
            raise Http404('No %s matches the given query.' % Resource._meta.object_name)

        return HttpResponse(resource.content, mimetype=u';charset='.join(resource.mimetype))


class Announce(View):
    def post(self, request):
        uuid = request.POST.get('uuid')
        ip_address = request.POST.get('ip_address')
        port = request.POST.get('port')
        logger.info('received announce call from: %s @ %s' % (uuid, request.META['REMOTE_ADDR']))
        if uuid and ip_address and port:
            sibling_data = {'ip_address': ip_address, 'port': port}
            # TODO: Verify node identity
            sibling, created = Sibling.objects.get_or_create(uuid=uuid, defaults=sibling_data)
            if not created:
                sibling.ip_address = sibling_data['ip_address']
                sibling.port = sibling_data['port']
                sibling.save()
            local_node = LocalNode.get()
            local_node_info = {
                'ip_address': IPADDRESS,
                'port': PORT,
                'uuid': local_node.uuid,
                'name': local_node.name,
                'email': local_node.email,
                'comment': local_node.comment,
            }
            return local_node_info
        else:
            return Response(status.PARTIAL_CONTENT)


class Heartbeat(View):
    def post(self, request):
        uuid = request.GET.get('uuid')
        # TODO: Reject call from non verified nodes
        logger.info('received heartbeat call from node: %s @ %s' % (uuid, request.META['REMOTE_ADDR']))
        return {'cpuload': CPUsage()}


class InventoryHash(View):
    def post(self, request):
        uuid = request.GET.get('uuid')
        # TODO: Reject call from non verified nodes
        logger.info('received inventory hash call from node: %s @ %s' % (uuid, request.META['REMOTE_ADDR']))
        return {'inventory_hash': HASH_FUNCTION(u''.join([version.full_uuid for version in Version.objects.all().order_by('timestamp')]))}


# Interactive views - user
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


def resource_list(request, fingerprint=None):
    resource_list = {}
    if fingerprint:
        network_resources = [NetworkResourceVersion.objects.get(uuid=resource['uuid']) for resource in NetworkResourceVersion.objects.filter(uuid__startswith=fingerprint).values('uuid').distinct().order_by()]
        local_resources = Resource.objects.filter(uuid__startswith=fingerprint)
        if network_resources:
            title = _(u'Resources from: %s') % network_resources[0].username
        elif local_resources:
            title = _(u'Resources from: %s') % local_resources[0].username
    else:
        network_resources = [NetworkResourceVersion.objects.get(uuid=resource['uuid']) for resource in NetworkResourceVersion.objects.values('uuid').distinct().order_by()]
        local_resources = Resource.objects.all()
        title = _(u'Resource list')

    for network_resource in network_resources:
        # Remove any timestamp
        resource_list[network_resource.uuid.split(TIMESTAMP_SEPARATOR)[0]] = network_resource

    for resource in local_resources:
        resource_list[resource.uuid] = resource

    return render_to_response('network_resource_list.html', {
        'object_list': resource_list,
        'title': title,
    }, context_instance=RequestContext(request))


def resource_publishers(request):
    publishers = {}
    network_resources = [NetworkResourceVersion.objects.get(uuid=resource['uuid']) for resource in NetworkResourceVersion.objects.values('uuid').distinct().order_by()]
    for network_resource in network_resources:
        if network_resource.username:
            username_dict = publishers.setdefault(network_resource.username, {})
            username_dict['fingerprint'] = network_resource.fingerprint

    for resource in Resource.objects.all():
        username_dict = publishers.setdefault(resource.username, {})
        username_dict['fingerprint'] = resource.fingerprint


    return render_to_response('network_resource_publishers.html', {
        'publishers': publishers,
        'title': _(u'Resources by publisher'),
    }, context_instance=RequestContext(request))
