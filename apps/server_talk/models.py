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
    port = models.PositiveIntegerField(blank=True, verbose_name=_(u'port'))
    #verified = models.BooleanField(verbose_name=_(u'verified'))  #GPG Key verified?
    last_heartbeat = models.DateTimeField(blank=True, default=datetime.datetime.now(), verbose_name=_(u'last heartbeat check'))
    cpuload = models.PositiveIntegerField(blank=True, default=0, verbose_name=_(u'cpu load'))
    last_inventory_hash = models.DateTimeField(blank=True, default=datetime.datetime.now(), verbose_name=_(u'last inventory check'))
    inventory_hash = models.CharField(max_length=64, blank=True, verbose_name=_(u'inventory hash'))

    class Meta(Nodebase.Meta):
        verbose_name = _(u'sibling node')
        verbose_name_plural = _(u'sibling nodes')


class Resource(ResourceBase):
    pass
    
    
class ResourceHolder(models.Model):
    resource = models.ForeignKey(Resource, verbose_name=_(u'resource'))
    node = models.ForeignKey(Sibling, verbose_name=_(u'Sibling'))
    
    def __unicode__(self):
        return unicode(self.node)
    
    class Meta:
        verbose_name = _(u'resource holder')
        verbose_name_plural = _(u'resource holders')
