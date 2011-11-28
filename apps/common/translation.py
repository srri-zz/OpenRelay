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
