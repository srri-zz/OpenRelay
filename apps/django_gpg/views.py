from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib import messages
from django.views.generic.list_detail import object_list
from django.core.urlresolvers import reverse

from django_gpg import Key
from django_gpg.forms import NewKeyForm

from core.runtime import gpg


def key_list(request, secret=True):
    if secret:
        object_list = Key.get_all(gpg, secret=True)
        title = _(u'Private key list')
    else:
        object_list = Key.get_all(gpg)
        title = _(u'Public key list')
        
    return render_to_response('key_list.html', {
        'object_list': object_list,
        'title': title,
    }, context_instance=RequestContext(request))
       

def key_create(request):
    if request.method == 'POST':
        form = NewKeyForm(request.POST)
        if form.is_valid():
            try:
                key = gpg.create_key(
                    name_real = form.cleaned_data['name'],
                    name_comment = form.cleaned_data['comment'],
                    name_email = form.cleaned_data['email'],
                )
                    
                    
                messages.success(request, _(u'Key: %s, created successfully.') % key)
                return HttpResponseRedirect(reverse('key_create'))
            except Exception, msg:
                messages.error(request, msg)
                return HttpResponseRedirect(reverse('key_create'))
    else:
        form = NewKeyForm()

    return render_to_response('generic_form.html', {
        'form': form,
        'title': _(u'Create a new key'),
    }, context_instance=RequestContext(request))    
