"""The root view for OpenRelay API"""
import logging
import hashlib
import psutil

from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.utils.simplejson import loads

#Latest djangorestframework stuff
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from openrelay_resources.models import Resource, Version
from serializers import ResourceSerializer

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

class OpenRelayAPI(APIView):
     """
    This is the REST API for OpenRelay (https://github.com/Captainkrtek/OpenRelay).
    """

    def get(self, request):
        return Response([
            {'name': 'Resources', 'url': reverse('resource_file-root')},
            {'name': 'Versions', 'url': reverse('version-root')},
            {'name': 'Siblings', 'url': reverse('sibling-root')},
            {'name': 'Announce', 'url': reverse('service-announce')},
            {'name': 'Heartbeat', 'url': reverse('service-heartbeat')},
            {'name': 'Inventory hash', 'url': reverse('service-inventory_hash')},
            {'name': 'Siblings hash', 'url': reverse('service-siblings_hash')},
        ])

class ResourceFileRoot(APIView):

    def post(self, request):
        return [
            {
                'uuid': resource.uuid,
                'url': reverse('resource_file', args=[resource.uuid]),
            }
            for resource in Resource.objects.all()
        ]


class Announce(APIView):

    def post(self, request):
        logger.info('received announce call from: %s' % request.META['REMOTE_ADDR'])
        signed_data = request.POST.get('signed_data')
        try:
            fingerprint, result = decrypt_request_data(signed_data)
        except NodeDataPackageError:
            logger.error('got NodeDataPackageError')
            return Response(status.BAD_REQUEST)
        else:
            logger.info('remote node uuid is: %s' % fingerprint)
            try:
                sibling_data = {'ip_address': result['ip_address'], 'port': result['port']}
            except KeyError:
                return Response(status.PARTIAL_CONTENT)
            else:
                sibling, created = Sibling.objects.get_or_create(uuid=fingerprint, defaults=sibling_data)
                if not created:
                    sibling.ip_address = sibling_data['ip_address']
                    sibling.port = sibling_data['port']
                    sibling.save()

                # Send our info
                local_node_info = {
                    'ip_address': IPADDRESS,
                    'port': PORT,
                }
                try:
                    return prepare_package(local_node_info)
                except KeyDoesNotExist:
                    return Response(status.INTERNAL_SERVER_ERROR)

class Heartbeat(APIView):

    def post(self, request):
        signed_data = request.POST.get('signed_data')
        try:
            fingerprint, result = decrypt_request_data(signed_data)
        except NodeDataPackageError:
            logger.error('got NodeDataPackageError')
            return Response(status.BAD_REQUEST)
        else:
            uuid = fingerprint

        logger.info('received heartbeat call from node: %s @ %s' % (uuid, request.META['REMOTE_ADDR']))
        return prepare_package({'cpuload': str(psutil.cpu_percent())})

class InventoryHash(APIView):

    def post(self, request):
        signed_data = request.POST.get('signed_data')
        try:
            fingerprint, result = decrypt_request_data(signed_data)
        except NodeDataPackageError:
            logger.error('got NodeDataPackageError')
            return Response(status.BAD_REQUEST)
        else:
            uuid = fingerprint

        logger.info('received inventory hash call from node: %s @ %s' % (uuid, request.META['REMOTE_ADDR']))
        return prepare_package(
            {
                'inventory_hash': HASH_FUNCTION(
                    u''.join([version.full_uuid for version in Version.objects.all().order_by('timestamp')])
                )
            }
        )


class ResourceFileObject(APIView):

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



class VersionRoot(APIView):

    def post(self, request):
        return prepare_package(
            {
                'version-list': [
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
            }
        )


class VersionObject(APIView):

    def post(self, request, uuid):
        version = Resource.objects.get(uuid=uuid)
        return Response({
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
        })


class ResourceDownload(APIView):

    def post(self, request, uuid):
        #logger.info('received resource download call from node: %s @ %s' % (node_uuid, request.META['REMOTE_ADDR']))
        try:
            resource = Resource.objects.get(uuid=uuid)
        except Resource.DoesNotExist:
            raise Http404('No %s matches the given query.' % Resource._meta.object_name)

        return HttpResponse(resource.download())


class ResourceServe(APIView):

    def post(self, request, uuid):
        #logger.info('received resource serve call from node: %s @ %s' % (node_uuid, request.META['REMOTE_ADDR']))
        try:
            resource = Resource.objects.get(uuid=uuid)
        except Resource.DoesNotExist:
            raise Http404('No %s matches the given query.' % Resource._meta.object_name)

        return HttpResponse(resource.content, mimetype=u';charset='.join(resource.mimetype))


class SiblingsHash(APIView):

    def post(self, request):
        signed_data = request.POST.get('signed_data')
        try:
            fingerprint, result = decrypt_request_data(signed_data)
        except NodeDataPackageError:
            logger.error('got NodeDataPackageError')
            return Response(status.BAD_REQUEST)
        else:
            uuid = fingerprint

        logger.info('received siblings hash call from node: %s' % uuid)
        return prepare_package(
            {
                'siblings_hash': HASH_FUNCTION(
                    u''.join(
                        [
                            node.uuid for node in Sibling.objects.all().order_by('uuid')
                        ]
                    )
                )
            }
        )

class SiblingList(APIView):

    def post(self, request):
        signed_data = request.POST.get('signed_data')
        try:
            fingerprint, result = decrypt_request_data(signed_data)
        except NodeDataPackageError:
            logger.error('got NodeDataPackageError')
            return Response(status.BAD_REQUEST)
        else:
            uuid = fingerprint

        logger.info('received siblings list call from node: %s' % uuid)
        return prepare_package(
            {
                'sibling_list': [
                    {
                        'uuid': sibling.uuid,
                        'ip_address': sibling.ip_address,
                        'port': sibling.port,
                        'last_heartbeat': sibling.last_heartbeat,
                        'cpuload': sibling.cpuload,
                        'status': sibling.status,
                        'failure_count': sibling.failure_count,
                        'last_inventory_hash': sibling.last_inventory_hash,
                        'inventory_hash': sibling.inventory_hash,
                        'last_siblings_hash': sibling.last_siblings_hash,
                        'siblings_hash': sibling.siblings_hash,
                    }
                    for sibling in Sibling.objects.all()
                ]
            }
        )


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
        'object_list': [LocalNode()],
        'title': _(u'Local node information'),
    }, context_instance=RequestContext(request))


def resource_list(request, fingerprint=None):
    resource_list = {}
    title = ""
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

