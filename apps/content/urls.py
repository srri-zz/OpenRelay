from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('content.views',
    url(r'^serve/$', 'serve_resource', (), 'serve_resource'),
)
