from django.conf.urls.defaults import patterns, url

from djangorestframework.views import ListModelView

from server_talk.resources import ResourceResource
from server_talk.views import OpenRelayAPI, ReadOnlyInstanceModelView, \
    Services, Announce, Heartbeat, InventoryHash


urlpatterns = patterns('',
    url(r'^$', OpenRelayAPI.as_view(), name='api-root'),
    url(r'^resource/$', ListModelView.as_view(resource=ResourceResource), name='resource-root'),
    url(r'^resource/(?P<uuid>[^/]+)/(?P<time_stamp>\d+)/$', ReadOnlyInstanceModelView.as_view(resource=ResourceResource), name='resource-full-url'),
    url(r'^resource/(?P<uuid>[^/]+)/$', ReadOnlyInstanceModelView.as_view(resource=ResourceResource)),

    url(r'^services/$', Services.as_view(), name='service-root'),
    url(r'^services/announce/$', Announce.as_view(), name='service-announce'),
    url(r'^services/heartbeat/$', Heartbeat.as_view(), name='service-heartbeat'),
    url(r'^services/inventory_hash/$', InventoryHash.as_view(), name='service-inventory_hash'),
)

urlpatterns += patterns('server_talk.views',
    url(r'^network/join/$', 'join', (), 'join'),
    url(r'^network/node/list/$', 'node_list', (), 'node_list'),
    url(r'^network/node/local/$', 'node_info', (), 'node_info'),
    url(r'^network/resource/list/$', 'resource_list', (), 'network_resource_list'),
)
