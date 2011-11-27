from django.template import TemplateSyntaxError, TokenParser, Library

from common import translation

register = Library()


def custom_language_name_local(lang_code):
    return translation.get_language_info(lang_code)['name_local']

register.filter(custom_language_name_local)
