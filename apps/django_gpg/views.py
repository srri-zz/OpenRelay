from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib import messages
from django.core.urlresolvers import reverse

from server_talk.api import NetworkCall
from server_talk.models import LocalNode
from queue_manager import Queue

from django_gpg import Key, KeyGenerationError
from django_gpg.forms import NewKeyForm, KeySelectionForm
    
from core.runtime import gpg


def key_list(request, secret=True):
    msg_queue = Queue(queue_name='gpg_msg_queue')
    while True:
        msg_data = msg_queue.pull()
        if not msg_data:
            break;
        messages.add_message(request, msg_data.get('tag', messages.INFO), msg_data['message'])
        
    if secret:
        object_list = Key.get_all(gpg, secret=True, exclude=LocalNode().public_key)
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
                key = gpg.create_key_background(
                    name_real=form.cleaned_data['name'],
                    name_comment=form.cleaned_data['comment'],
                    name_email=form.cleaned_data['email'],
                    passphrase=form.cleaned_data['passphrase'],
                    key_type=form.cleaned_data['key_primary_class'],
                    key_length=form.cleaned_data['key_primary_size'],
                    subkey_type=form.cleaned_data['key_secondary_class'],
                    subkey_length=form.cleaned_data['key_secondary_size'],
                    expire_date=form.cleaned_data['expiration'],
                )
                messages.success(request, _(u'Key pair queued for creation, refresh this page to check results.'))
                return HttpResponseRedirect(reverse('key_private_list'))
            except KeyGenerationError, msg:
                messages.error(request, msg)
                return HttpResponseRedirect(reverse('key_create'))
    else:
        form = NewKeyForm()

    return render_to_response('generic_form.html', {
        'form': form,
        'title': _(u'Create a new key'),
        'message': _(u'The key creation process can take quite some time to complete, please be patient.')
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
        'message': _(u'Are you sure you wish to delete key:%s?  If you try to delete a public key that is part of a public/private pair the private key will be deleted as well.') % Key.get(gpg, fingerprint)
    }, context_instance=RequestContext(request))

    
def key_publish(request):
    if request.method == 'POST':
        form = KeySelectionForm(request.POST)
        if form.is_valid():
            try:
                network = NetworkCall()
                key = Key.get(gpg, form.cleaned_data['key'])
                network.publish_key(key)
                messages.success(request, _(u'Key publish request for key: %s, has been sent') % key)
                return HttpResponseRedirect(reverse('home_view'))
            except AnnounceClientError:
                messages.error(request, _(u'Unable to send key publish call'))
                return HttpResponseRedirect(reverse('key_publish'))
    else:
        form = KeySelectionForm()

    return render_to_response('generic_form.html', {
        'form': form,
        'title': _(u'Publish a key to the OpenRelay network'),
    }, context_instance=RequestContext(request))       
