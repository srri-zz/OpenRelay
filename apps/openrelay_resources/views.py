import logging

from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib import messages
from django.core.urlresolvers import reverse

from django_gpg import GPGSigningError, Key
from core.runtime import gpg

from server_talk.api import NetworkCall
from server_talk.exceptions import NetworkResourceNotFound

from openrelay_resources.forms import ResourceForm
from openrelay_resources.models import Resource, Version
from openrelay_resources.compressed_file import CompressedFile, NotACompressedFile

logger = logging.getLogger(__name__)

def _get_object_or_404(model, *args, **kwargs):
    """
    Custom get_object_or_404 as the Django one call .get() method on a
    QuerySet thus ignoring a custom manager's .get() method
    """
    try:
        return model.objects.get(*args, **kwargs)
    except model.DoesNotExist:
        raise Http404('No %s matches the given query.' % model._meta.object_name)


def resource_serve(request, uuid):
    try:
        resource = Resource.objects.get(uuid=uuid)
    except Resource.DoesNotExist:
        network = NetworkCall()
        try:
            resource = network.find_resource(uuid)
        except NetworkResourceNotFound, msg:
            raise Http404(msg)

    return HttpResponse(resource.content, mimetype=u';charset='.join(resource.mimetype))


def resource_upload(request):
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            file=request.FILES['file']
            uncompress=form.cleaned_data['uncompress']
            filter_html = form.cleaned_data['filter_html']
            key = Key.get(gpg, form.cleaned_data['key'])
            name = form.cleaned_data['name']
            label = form.cleaned_data['label']
            description = form.cleaned_data['description']

            try:
                if uncompress:
                    try:
                        cf = CompressedFile(file)
                        unzippedfiles = []
                        for fp in cf.children():
                            unzippedfile = Resource()
                            unzippedfile.upload(
                                file = fp,
                                key = key,
                                name = name,
                                label = label,
                                description = description,
                                filter_html = filter_html,
                                uncompress = uncompress,
                                usefilename = False,
                            )
                            fp.close()
                            unzippedfiles.append(unzippedfile)
                        namelist = ""
                        for name in unzippedfiles:
                            namelist += name.uuid + "; "
                        messages.success(request, _(u'Resource(s): %s, created successfully.') % namelist)
                        cf.close()
                    except NotACompressedFile:
                        # Reset the file descriptor
                        file.seek(0)
                        resource = Resource()
                        resource.upload(
                            file = file,
                            key = key,
                            name = name,
                            label = label,
                            description = description,
                            filter_html = filter_html,
                            uncompress = uncompress,
                            usefilename = True,
                        )
                        messages.success(request, _(u'Resource: %s, created successfully.') % resource)
                else:
                    resource = Resource()
                    resource.upload(
                        file = file,
                        key = key,
                        name = name,
                        label = label,
                        description = description,
                        filter_html = filter_html,
                        uncompress = uncompress,
                        usefilename = True,
                    )
                    messages.success(request, _(u'Resource: %s, created successfully.') % resource)
                return HttpResponseRedirect(reverse('resource_upload'))
            except GPGSigningError, msg:
                messages.error(request, msg)
                return HttpResponseRedirect(reverse('resource_upload'))
    else:
        form = ResourceForm()

    return render_to_response('generic_form.html', {
        'form': form,
        'title': _(u'Create a new resource'),
    }, context_instance=RequestContext(request))


def resource_list(request):
    query_set = [Resource.objects.get(uuid=resource['uuid']) for resource in Resource.objects.values('uuid').distinct().order_by()]
    return render_to_response('resource_list.html', {
        'object_list': Resource.objects.all()
    }, context_instance=RequestContext(request))
    
    
def resource_details(request, uuid):
    return render_to_response('resource_details.html', {
        'resource': get_object_or_404(Resource, uuid=uuid),
    }, context_instance=RequestContext(request))
