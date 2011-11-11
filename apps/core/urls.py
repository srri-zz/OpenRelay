from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import direct_to_template
from django.conf import settings

from core import __version__

urlpatterns = patterns('core.views',
    url(r'^$', direct_to_template, {'template': 'home.html'}, 'home_view'),
    url(r'^about/$', direct_to_template, {'template': 'about.html', 'extra_context': {'version': __version__}}, 'about_view'),
    #url(r'^changelog/$', 'changelog_view', (), 'changelog_view'),
    #url(r'^license/$', 'license_view', (), 'license_view'),
)

#urlpatterns += patterns('',
    #(r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '%s%s' % (settings.STATIC_URL, 'images/favicon.ico')}),
#)
