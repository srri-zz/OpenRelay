from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('openrelay_resources.views',
    url(r'^serve/(?P<uuid>.+)/(?P<time_stamp>\d+)/$', 'resource_serve', (), 'resource_serve'),
    url(r'^serve/(?P<uuid>.+)/$', 'resource_serve', (), 'resource_serve'),
    url(r'^upload/$', 'resource_upload', (), 'resource_upload'),
    url(r'^list/$', 'resource_list', (), 'resource_list'),
)
