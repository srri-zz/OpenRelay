from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib import messages
from django.views.generic.list_detail import object_list
from django.core.urlresolvers import reverse
from django.utils.http import urlencode

from bittorrent.api import fetch_torrent


def download_torrent(request):
    #fetch_torrent(
    messages.success(request, 'Downloading sample torrent')
    
    return HttpResponseRedirect(reverse('home_view', args=[]))
    
