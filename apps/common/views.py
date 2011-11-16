import urlparse
import types

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.utils.translation import ugettext_lazy as _
from django.contrib import messages
from django.utils.importlib import import_module

# Avoid shadowing the login() and logout() views below.
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login, logout as auth_logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.sites.models import get_current_site

SETTINGS_LIST = (
    ('openrelay_resources', 'STORAGE_BACKEND', 'RESOURCES_STORAGE_BACKEND'),
    ('openrelay_resources', 'FILESTORAGE_LOCATION', 'RESOURCES_FILESTORAGE_LOCATION'),
    ('core', 'KEYSERVERS', 'CORE_KEYSERVERS'),
    ('server_talk', 'PORT', 'SERVER_PORT'),
)


@csrf_protect
@never_cache
def login_view(request, template_name='login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm,
          current_app=None, extra_context=None):
    """
    Displays the login form and handles the login action.
    """
    redirect_to = request.REQUEST.get(redirect_field_name, '')

    if request.method == "POST":
        form = authentication_form(data=request.POST)
        if form.is_valid():
            netloc = urlparse.urlparse(redirect_to)[1]

            # Use default setting if redirect_to is empty
            if not redirect_to:
                redirect_to = settings.LOGIN_REDIRECT_URL

            # Security check -- don't allow redirection to a different
            # host.
            elif netloc and netloc != request.get_host():
                redirect_to = settings.LOGIN_REDIRECT_URL

            # Okay, security checks complete. Log the user in.
            auth_login(request, form.get_user())

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()
        else:
            messages.error(request, ugettext(u'Incorrent username or password.'))

    request.session.set_test_cookie()

    current_site = get_current_site(request)

    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
    }
    context.update(extra_context or {})
    return HttpResponseRedirect(reverse('home_view'))


def return_type(value):
    if isinstance(value, types.FunctionType):
        return value.__doc__ if value.__doc__ else _(u'function found')
    elif isinstance(value, types.ClassType):
        return _(u'class found: %s') % unicode(value).split("'")[1].split('.')[-1]
    elif isinstance(value, types.TypeType):
        return _(u'class found: %s') % unicode(value).split("'")[1].split('.')[-1]
    elif isinstance(value, types.DictType) or isinstance(value, types.DictionaryType):
        return ','.join(list(value))
    else:
        return value


def settings_list(request):
    object_list = []
    for setting in SETTINGS_LIST:
        module = import_module('.settings', '%s.conf' % setting[0])
        object_list.append(
            {
                'app': setting[0],
                'global_name': setting[2],
                'value': return_type(getattr(module, setting[1], None))
            }
        )

    return render_to_response('settings_list.html', {'object_list': object_list},
        context_instance=RequestContext(request))
