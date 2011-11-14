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
                    passphrase = form.cleaned_data['passphrase'],
                )

                messages.success(request, _(u'Key pair: %s, created successfully.') % key.fingerprint)
                return HttpResponseRedirect(reverse('key_create'))
            except Exception, msg:
                messages.error(request, msg)
                return HttpResponseRedirect(reverse('key_create'))
    else:
        form = NewKeyForm()

    return render_to_response('generic_form.html', {
        'form': form,
        'title': _(u'Create a new key'),
        'message': _(u'The key creation process can take a few minutes, don\'t close or browse another page until it has finished.')
    }, context_instance=RequestContext(request))
    
    
def key_delete(request, fingerprint, key_type):
    if request.method == 'POST':
        try:
            secret = key_type == 'sec'
            key = Key.get(gpg, fingerprint, secret=secret)
            gpg.delete_key(key)
            messages.success(request, _(u'Key: %s, deleted successfully.') % fingerprint)
            return HttpResponseRedirect(reverse('home_view'))
        except Exception, msg:
            messages.error(request, msg)
            return HttpResponseRedirect(reverse('home_view'))

    return render_to_response('generic_confirm.html', {
        'title': _(u'Delete key'),
        'message': _(u'Are you sure you wish to delete key:%s?  If you try to delete a public key that is part of a public/private pair the private key will be deleted as well.') %  Key.get(gpg, fingerprint)
    }, context_instance=RequestContext(request))
