import datetime
import socket

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.simplejson import dumps, loads

from openrelay_resources.models import ResourceBase, VersionBase
from openrelay_resources.literals import TIMESTAMP_SEPARATOR

from server_talk.conf.settings import PORT
from server_talk.literals import NODE_STATUS_DOWN, NODE_STATUS_CHOICES


class Nodebase(models.Model):
    uuid = models.CharField(max_length=48, editable=False, verbose_name=_(u'UUID'))
    name = models.CharField(max_length=255, editable=False, verbose_name=_(u'name'))
    email = models.CharField(max_length=255, editable=False, verbose_name=_(u'e-mail'))
    comment = models.CharField(max_length=255, editable=False, verbose_name=_(u'comment'))

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
    status = models.PositiveIntegerField(choices=NODE_STATUS_CHOICES, default=NODE_STATUS_DOWN, verbose_name=_(u'status'))
    failure_count = models.PositiveIntegerField(default=0, verbose_name=_('failure count'))
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
    uuid = models.CharField(max_length=48, blank=True, verbose_name=_(u'UUID'), editable=False)
    timestamp = models.PositiveIntegerField(verbose_name=_(u'timestamp'), db_index=True, editable=False)
    metadata = models.TextField(blank=True, verbose_name=_(u'metadata'), editable=False)
    signature_properties = models.TextField(blank=True, verbose_name=_(u'signature properties'), editable=False)
    
    objects = NetworkResourceVersionManager()

    def __getattr__(self, name):
        signature_properties_list = ['is_valid', 'signature_status', 'username', 'signature_id', 'raw_timestamp', 'timestamp_display', 'fingerprint', 'key_id']
        metadata_attributes_list = ['name', 'label', 'description']
        
        if name in signature_properties_list:
            try:
                return loads(self.signature_properties)[name]
            except KeyError, msg:
                # Convert KeyError exception into an AttributeError
                # as we are simulating class properties
                raise AttributeError(msg)
        elif name in metadata_attributes_list:
            # Don't raise KeyError or AttributeError exception for a
            # non existant value on 'label' or 'description' as these are
            # blank by default 
            return loads(self.metadata).get(name, u'')
        else:
            raise AttributeError

    def __unicode__(self):
        return self.uuid
        
    def full_uuid(self):
        return VersionBase.prepare_full_resource_name(self.uuid, self.timestamp)
    
    @property
    def formated_timestamp(self):
        return datetime.datetime.fromtimestamp(self.timestamp)
        
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
