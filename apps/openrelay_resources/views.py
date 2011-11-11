#import sendfile

from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib import messages
from django.views.generic.list_detail import object_list
from django.core.urlresolvers import reverse

from resources.forms import ResourceForm
from resources.models import Resource


def resource_serve(request, uuid, time_stamp=None):
    print uuid
    if time_stamp:
        resource = get_object_or_404(Resource, uuid=uuid, time_stamp=time_stamp)
    else:
        qs = Resource.objects.filter(uuid=uuid)
        if not qs:
            raise Http404('No Resource matches the given query.')
        else:
            resource = qs[0]
        
    response = HttpResponse(resource.extract(), mimetype=u';charset='.join(resource.mimetype))
    return response


def resource_upload(request):
    if request.method == 'POST':
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.save(key=form.cleaned_data['key'], name=form.cleaned_data['name'])
            messages.success(request, _(u'Resource created successfully.'))
            return HttpResponseRedirect(reverse('resource_upload'))
    else:
        form = ResourceForm()

    return render_to_response('generic_form.html', {
        'form': form,
        'title': _(u'Create a new resource'),
    }, context_instance=RequestContext(request))


def resource_list(request):
    return object_list(
        request,
        queryset=Resource.objects.all(),
        template_name='resource_list.html',
    )
