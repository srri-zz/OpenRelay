from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import direct_to_template
from django.conf import settings

urlpatterns = patterns('common.views',
    #url(r'^password/change/done/$', 'password_change_done', (), name='password_change_done'),
    #url(r'^user/$', 'current_user_details', (), 'current_user_details'),
    #url(r'^user/edit/$', 'current_user_edit', (), 'current_user_edit'),

    url(r'^login/$', 'login_view', (), name='login_view'),
)

urlpatterns += patterns('',
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='logout_view'),
)
