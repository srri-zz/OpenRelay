import re
import locale
import os

from django.utils.translation.trans_real import (check_for_language,
    all_locale_paths, parse_accept_lang_header, to_locale)

_accepted = {}


def get_language_info(lang_code):
    from django.conf.locale import LANG_INFO
    # Add custom languages
    LANG_INFO.update(
        {
            'tlh': {
                'bidi': False,
                'code': 'tlh',
                'name': 'Klingon',
                'name_local': u'tlhIngan Hol',# \uf8e4\uf8d7\uf8dc\uf8db \uf8d6\uf8dd\uf8d9',
            },
            'cs-cz': {
                'bidi': False,
                'code': 'cs',
                'name': 'Czech',
                'name_local': u'\u010desky (\u010cesk\xe1 republika)',
            },
        }
    )

    try:
        return LANG_INFO[lang_code]
    except KeyError:
        raise KeyError("Unknown language code %r." % lang_code)


def get_language_from_request(request):
    """
    Analyzes the request to find what language the user wants the system to
    show. Only languages listed in settings.LANGUAGES are taken into account.
    If the user requests a sublanguage where we have a main language, we send
    out the main language.
    """
    global _accepted
    from django.conf import settings
    supported = dict(settings.LANGUAGES)

    if hasattr(request, 'session'):
        lang_code = request.session.get('django_language', None)
        if lang_code in supported and lang_code is not None: # and check_for_language(lang_code):
            return lang_code

    lang_code = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)

    if lang_code and lang_code not in supported:
        lang_code = lang_code.split('-')[0] # e.g. if fr-ca is not supported fallback to fr

    if lang_code and lang_code in supported and check_for_language(lang_code):
        return lang_code

    accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    for accept_lang, unused in parse_accept_lang_header(accept):
        if accept_lang == '*':
            break

        # We have a very restricted form for our language files (no encoding
        # specifier, since they all must be UTF-8 and only one possible
        # language each time. So we avoid the overhead of gettext.find() and
        # work out the MO file manually.

        # 'normalized' is the root name of the locale in POSIX format (which is
        # the format used for the directories holding the MO files).
        normalized = locale.locale_alias.get(to_locale(accept_lang, True))
        if not normalized:
            continue
        # Remove the default encoding from locale_alias.
        normalized = normalized.split('.')[0]

        if normalized in _accepted:
            # We've seen this locale before and have an MO file for it, so no
            # need to check again.
            return _accepted[normalized]

        for lang, dirname in ((accept_lang, normalized),
                (accept_lang.split('-')[0], normalized.split('_')[0])):
            if lang.lower() not in supported:
                continue
            for path in all_locale_paths():
                if os.path.exists(os.path.join(path, dirname, 'LC_MESSAGES', 'django.mo')):
                    _accepted[normalized] = lang
                    return lang

    return settings.LANGUAGE_CODE

dot_re = re.compile(r'\S')
