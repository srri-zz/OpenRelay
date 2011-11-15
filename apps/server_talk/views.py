"""The root view for OpenRelay API"""

from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.contrib import messages
from django.core.urlresolvers import reverse

from djangorestframework.mixins import InstanceMixin, ReadModelMixin
from djangorestframework.views import View, ModelView

from server_talk.models import LocalNode


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
        return [{'name': 'Announce', 'url': reverse('service-announce')}]


class Announce(View):
    def post(self, request):
        return {'uuid': LocalNode.get().uuid}


#def join(request):
    #request.POST
    
#def inventory_view(request):
