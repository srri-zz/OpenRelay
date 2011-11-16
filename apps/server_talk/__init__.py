import uuid

from django.db.models.signals import post_syncdb
from django.core.signals import request_finished
from django.dispatch import receiver

from server_talk.models import LocalNode
from server_talk import models as server_talk_model


@receiver(post_syncdb, dispatch_uid='create_identify', sender=server_talk_model)
def create_identify(sender, **kwargs):
    print 'Creating local node identity ...'
    info, created = LocalNode.objects.get_or_create(lock_id='1', defaults={'uuid': unicode(uuid.uuid4())})
    if not created:
        print 'Existing identify not modified.'
