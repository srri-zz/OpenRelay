from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('bittorrent.views',
    url(r'^download_torrent/$', 'download_torrent', (), 'download_torrent'),
)
