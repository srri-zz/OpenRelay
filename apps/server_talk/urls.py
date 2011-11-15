from django.conf.urls.defaults import patterns, url

from djangorestframework.views import ListModelView

from server_talk.resources import ResourceResource
from server_talk.views import OpenRelayAPI, ReadOnlyInstanceModelView, Services, Announce


urlpatterns = patterns('',
    url(r'^$', OpenRelayAPI.as_view(), name='api-root'),
    url(r'^resource/$', ListModelView.as_view(resource=ResourceResource), name='resource-root'),
    url(r'^resource/(?P<uuid>[^/]+)/(?P<time_stamp>\d+)/$', ReadOnlyInstanceModelView.as_view(resource=ResourceResource), name='resource-full-url'),
    url(r'^resource/(?P<uuid>[^/]+)/$', ReadOnlyInstanceModelView.as_view(resource=ResourceResource)),

    url(r'^services/$', Services.as_view(), name='service-root'),
    url(r'^services/announce/$', Announce.as_view(), name='service-announce'),
)
