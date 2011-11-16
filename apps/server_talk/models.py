import datetime
import socket

from django.db import models
from django.utils.translation import ugettext_lazy as _

from openrelay_resources.models import ResourceBase

from server_talk.conf.settings import PORT


class Nodebase(models.Model):
    uuid = models.CharField(max_length=48, editable=False, verbose_name=_(u'UUID'))

    def __unicode__(self):
        return self.uuid

    class Meta:
        abstract = True
        verbose_name = _(u'node')
        verbose_name_plural = _(u'nodes')


class LocalNode(Nodebase):
    lock_id = models.CharField(max_length=1, default='1', editable=False, verbose_name=_(u'lock field'), unique=True)

    @classmethod
    def get(cls):
        return cls.objects.get(lock_id='1')

    def save(self, *args, **kwargs):
        self.id = 1
        super(LocalNode, self).save()

    def delete(self):
        pass

    @property
    def ip_address(self):
        return socket.gethostbyname(socket.gethostname())

    @property
    def port(self):
        return PORT

    class Meta(Nodebase.Meta):
        verbose_name = _(u'local node')
        verbose_name_plural = _(u'local node')


class Sibling(Nodebase):
    ip_address = models.IPAddressField(verbose_name=_(u'URL'))
    port = models.PositiveIntegerField(verbose_name=_(u'port'))
    #verified = models.BooleanField(verbose_name=_(u'verified'))

    class Meta(Nodebase.Meta):
        verbose_name = _(u'sibling node')
        verbose_name_plural = _(u'sibling nodes')


class Resource(ResourceBase):
    pass
