from django.core.urlresolvers import reverse
from django.http import HttpResponse

from djangorestframework.resources import ModelResource

from openrelay_resources.models import Resource


class ResourceResource(ModelResource):
    model = Resource
    fields = ('full_url', 'url', 'uuid', 'time_stamp', 'metadata')#, 'download')
    #ordering = ('created',)

    def full_url(self, instance):
        return reverse('resource-full-url', kwargs={
            'uuid': instance.uuid,
            'time_stamp': instance.time_stamp
        })

    #def download(self, instance):
    #    return reverse('resource-download', args=[instance.uuid]),
