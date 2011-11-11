"""The root view for OpenRelay API"""

from django.core.urlresolvers import reverse

from djangorestframework.mixins import InstanceMixin, ReadModelMixin
from djangorestframework.views import View, ModelView


class OpenRelayAPI(View):
    """This is the REST API for OpenRelay (https://github.com/Captainkrtek/OpenRelay).

    All the API calls allow anonymous access, and can be navigated either through the browser or from the command line...

        bash: curl -X GET http://127.0.0.1:8000/api/                           # (Use default renderer)
        bash: curl -X GET http://127.0.0.1:8000/api/ -H 'Accept: text/plain'   # (Use plaintext documentation renderer)

    """

    def get(self, request):
        return [{'name': 'Resources', 'url': reverse('resource-root')}]


class ReadOnlyInstanceModelView(InstanceMixin, ReadModelMixin, ModelView):
    """A view which provides default operations for read only against a model instance."""
    _suffix = 'Instance'
