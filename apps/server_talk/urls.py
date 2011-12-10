from django.conf.urls.defaults import patterns, url

from djangorestframework.views import ListModelView

from server_talk.views import (OpenRelayAPI, Announce, Heartbeat, 
    InventoryHash, ResourceFileRoot, ResourceFileObject, VersionObject,
    VersionRoot, ResourceDownload, ResourceServe, SiblingsHash, SiblingList)

urlpatterns = patterns('',
    url(r'^$', OpenRelayAPI.as_view(), name='api-root'),
    url(r'^resources/resource_file/(?P<uuid>.+)/$', ResourceFileObject.as_view(), name='resource_file'),
    url(r'^resources/resource_file/$', ResourceFileRoot.as_view(), name='resource_file-root'),
    url(r'^resources/version/download/(?P<uuid>.+)/$', ResourceDownload.as_view(), name='version-download'),
    url(r'^resources/version/serve/(?P<uuid>.+)/$', ResourceServe.as_view(), name='version-serve'),
    url(r'^resources/version/(?P<uuid>.+)/$', VersionObject.as_view(), name='version'),
    url(r'^resources/version/$', VersionRoot.as_view(), name='version-root'),
    url(r'^services/announce/$', Announce.as_view(), name='service-announce'),
    url(r'^services/heartbeat/$', Heartbeat.as_view(), name='service-heartbeat'),
    url(r'^services/inventory/hash/$', InventoryHash.as_view(), name='service-inventory_hash'),
    url(r'^services/siblings/hash/$', SiblingsHash.as_view(), name='service-siblings_hash'),
    url(r'^services/siblings/list/$', SiblingList.as_view(), name='service-siblings_list'),
)

urlpatterns += patterns('server_talk.views',
    url(r'^network/join/$', 'join', (), 'join'),
    url(r'^network/node/list/$', 'node_list', (), 'node_list'),
    url(r'^network/node/local/$', 'node_info', (), 'node_info'),
    url(r'^network/resource/list/all/$', 'resource_list', (), 'network_resource_list'),
    url(r'^network/resource/list/(?P<fingerprint>.+)/$', 'resource_list', (), 'network_resource_list'),
    url(r'^network/resource/publishers/$', 'resource_publishers', (), 'resource_publishers'),
)
