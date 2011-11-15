from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib import messages
from django.views.generic.list_detail import object_list
from django.core.urlresolvers import reverse

from django_gpg import GPGSigningError

from openrelay_resources.forms import ResourceForm
from openrelay_resources.models import Resource


def _get_object_or_404(model, *args, **kwargs):
    """
    Custom get_object_or_404 as the Django one call .get() method on a
    QuerySet thus ignoring a custom manager's .get() method
    """
    try:
        return model.objects.get(*args, **kwargs)
    except model.DoesNotExist:
        raise Http404('No %s matches the given query.' % model._meta.object_name)


def resource_serve(request, uuid, time_stamp=None):
    if time_stamp:
        resource = _get_object_or_404(Resource, uuid=uuid, time_stamp=time_stamp)
    else:
        resource = _get_object_or_404(Resource, uuid=uuid)

    response = HttpResponse(resource.content, mimetype=u';charset='.join(resource.mimetype))
    return response


def resource_upload(request):
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            pending_resource = form.save(commit=False)
            try:
                resource = pending_resource.save(
                    key=form.cleaned_data['key'],
                    name=form.cleaned_data['name'],
                    label=form.cleaned_data['label'],
                    description=form.cleaned_data['description'],
                    filter_html=form.cleaned_data['filter_html']
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


def resource_list(request, simple=True):
    if simple:
        query_set = [Resource.objects.get(uuid=resource['uuid']) for resource in Resource.objects.values('uuid').distinct().order_by()]
        template_name='resource_list_simple.html'        
    else:
        query_set = Resource.objects.all()
        template_name='resource_list.html'

    return render_to_response(template_name, {
        'object_list': query_set,
    }, context_instance=RequestContext(request))
        

    return object_list(
        request,
        queryset=query_set,
        template_name=template_name,
    )
