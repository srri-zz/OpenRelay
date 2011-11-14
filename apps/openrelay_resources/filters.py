import urlparse

from django.utils.encoding import smart_unicode, force_unicode, smart_str, DjangoUnicodeDecodeError

from bs4 import BeautifulSoup
from HTMLParser import HTMLParseError

import magic


class FilterError(Exception):
    pass
    

class FilteredHTML(object):        
    @staticmethod
    def is_external_top_level_link(url):
        scheme, netloc, path, qs, anchor = urlparse.urlsplit(url)
        if not path or path == '/':
            return True
        else:
            return False

    def fix_relative_url(self, url):
        scheme, netloc, path, qs, anchor = urlparse.urlsplit(url)
        if not netloc and path != '/':
            return self.url_filter(path)

        return url

    def fix_links(self):
        for tag in self.soup.findAll(attrs={'src': True}):
            if tag['src']:
                tag['src'] = self.fix_relative_url(tag['src'])

        for tag in self.soup.findAll(attrs={'href': True}):
            if tag['href'] and tag['href'] != '#':
                # A single '#' usually means a Javascript dynamic link,
                # don't touch it
                tag['href'] = self.fix_relative_url(tag['href'])

    def __init__(self, data, prettify=False, *args, **kwargs):
        self.url_filter = kwargs.pop('url_filter', lambda x:x)
        self.prettify = prettify
        magic_mime = magic.Magic(mime=True)

        if magic_mime.from_buffer(data) != 'text/html':
            raise FilterError('Non HTML data')
        
        #magic_encoding = magic.Magic(mime_encoding=True)
        #if magic_encoding.from_buffer(data) !='utf-8':
        
        try:
            self.data = smart_unicode(data)
        except DjangoUnicodeDecodeError:
            self.data = data

        try:
            self.soup = BeautifulSoup(self.data)

            self.fix_links()
            
            if self.prettify:
                self.html = soup.prettify()
            else:
                self.html = unicode(self.soup)
                
        #except (HTMLParseError, UnicodeDecodeError, RuntimeError):
        except HTMLParseError, msg:
            raise FilterError(msg)
            
    def __str__(self):
        return str(self.html)

    def __unicode__(self):
        return self.html

    def __repr__(self):
        return self.__unicode__()
