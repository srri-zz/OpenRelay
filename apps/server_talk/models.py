import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _

from openrelay_resources.models import ResourceBase


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
        self.id=1
        super(LocalNode, self).save()

    def delete(self):
        pass

    class Meta(Nodebase.Meta):
        verbose_name = _(u'local node')
        verbose_name_plural = _(u'local node')
    

class Sibling(Nodebase):
    ip_address = models.IPAddressField(verbose_name=_(u'IP address'))


class Resource(ResourceBase):
    pass


#class AnnounceQueue(models.Model):
    #datetime = models.DateTimeField(verbose_name=_(u'datetime received'))
    #node = 
    
    
    
    
    
