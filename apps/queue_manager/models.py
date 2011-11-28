from datetime import datetime

from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.simplejson import loads, dumps
from django.db import IntegrityError


class QueueException(Exception):
    pass

    
class QueuePushError(QueueException):
    pass


class Queue(models.Model):
    name = models.CharField(max_length=32, verbose_name=_(u'name'))
    label = models.CharField(blank=True, max_length=64, verbose_name=_(u'label'))
    unique_names = models.BooleanField(verbose_name=_(u'unique names'), default=False)

    def __unicode__(self):
        return self.label if self.label else self.name

    def push(self, name, data):
        queue_item = QueueItem(queue=self, name=name, data=dumps(data))
        queue_item.save()
        return queue_item
        
    def pull(self):
        queue_item_qs = QueueItem.objects.filter(queue=self).order_by('-creation_datetime')
        if queue_item_qs:
            queue_item = queue_item_qs[0]
            queue_item.delete()
            return loads(queue_item.data)
        
    class Meta:
        verbose_name = _(u'queue')
        verbose_name_plural = _(u'queues')


class QueueItem(models.Model):
    queue = models.ForeignKey(Queue, verbose_name=_(u'queue'))
    creation_datetime = models.DateTimeField(verbose_name=_(u'creation datetime'), editable=False)
    unique_name = models.CharField(blank=True, max_length=32, verbose_name=_(u'name'), unique=True, editable=False)
    name = models.CharField(blank=True, max_length=32, verbose_name=_(u'name'))
    data = models.TextField(verbose_name=_(u'data'))
    
    def __unicode__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self.creation_datetime = datetime.now()

        if self.queue.unique_names:
            self.unique_name = self.name
        else:
            self.unique_name = unicode(self.creation_datetime)
        try:
            super(QueueItem, self).save(*args, **kwargs)
        except IntegrityError:
            raise QueuePushError
    
    class Meta:
        verbose_name = _(u'queue item')
        verbose_name_plural = _(u'queue items')
    
