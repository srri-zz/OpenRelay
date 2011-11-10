from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('content.views',
    url(r'^serve/(?P<resource_id>[\d\w]+)/$', 'serve_resource', (), 'serve_resource'),
    url(r'^upload/$', 'resource_upload', (), 'resource_upload'),
    url(r'^list/$', 'resource_list', (), 'resource_list'),
    #url(r'^update/(?P<resource_id>[\d\w]+)/$', 'upload_resource', (), 'update_resource'),
)
