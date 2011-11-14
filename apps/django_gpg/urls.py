from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('django_gpg.views',
    #url(r'^serve/(?P<uuid>.+)/(?P<time_stamp>\d+)/$', 'resource_serve', (), 'resource_serve'),
    #url(r'^serve/(?P<uuid>.+)/$', 'resource_serve', (), 'resource_serve'),
    #url(r'^serve/$', 'resource_serve', (), 'resource_serve'),
    #url(r'^upload/$', 'resource_upload', (), 'resource_upload'),
    url(r'^create/$', 'key_create', (), 'key_create'),
    url(r'^list/private/$', 'key_list', {'secret': True}, 'key_private_list'),
    url(r'^list/public/$', 'key_list', {'secret': False}, 'key_public_list'),
)
