from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('openrelay_resources.views',
    url(r'^serve/(?P<uuid>.+)/(?P<time_stamp>\d+)/$', 'resource_serve', (), 'resource_serve'),
    url(r'^serve/(?P<uuid>.+)/$', 'resource_serve', (), 'resource_serve'),
    url(r'^serve/$', 'resource_serve', (), 'resource_serve'),
    url(r'^upload/$', 'resource_upload', (), 'resource_upload'),
    url(r'^list/simple/$', 'resource_list', {'simple': True}, 'resource_list_simple'),
    url(r'^list/$', 'resource_list', {'simple': False}, 'resource_list'),
)
