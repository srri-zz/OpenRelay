import datetime
import socket

from django.db import models
from django.utils.translation import ugettext_lazy as _

from openrelay_resources.models import ResourceBase, VersionBase
from openrelay_resources.literals import TIMESTAMP_SEPARATOR

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
    '''
    This class holds information of the currenty node, the "self" node, 
    and it is a singleton model
    '''
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


class NetworkResourceVersionManager(models.Manager):
    def get(self, uuid):
        try:
            simple_uuid, timestamp = uuid.split(TIMESTAMP_SEPARATOR)
            return super(NetworkResourceVersionManager, self).get(uuid=simple_uuid, timestamp=timestamp)
        except ValueError:
            try:
                return super(NetworkResourceVersionManager, self).filter(uuid=uuid).order_by('-timestamp')[0]
            except IndexError:
                raise self.model.DoesNotExist


class NetworkResourceVersion(models.Model):
    uuid = models.CharField(max_length=48, blank=True, editable=False, verbose_name=_(u'UUID'))
    timestamp = models.PositiveIntegerField(verbose_name=_(u'timestamp'), db_index=True, editable=False)
    
    objects = NetworkResourceVersionManager()

    def __unicode__(self):
        return self.uuid
        
    def full_uuid(self):
        return VersionBase.prepare_full_resource_name(self.uuid, self.timestamp)
        
    class Meta(Nodebase.Meta):
        verbose_name = _(u'network resource version')
        verbose_name_plural = _(u'network resource versions')

    
class ResourceHolder(models.Model):
    resource_version = models.ForeignKey(NetworkResourceVersion, verbose_name=_(u'resource version'))
    node = models.ForeignKey(Sibling, verbose_name=_(u'Sibling'))
    
    def __unicode__(self):
        return unicode(self.node)
    
    class Meta:
        verbose_name = _(u'resource holder')
        verbose_name_plural = _(u'resource holders')
