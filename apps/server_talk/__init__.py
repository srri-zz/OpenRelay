import logging
import uuid

from django.db.models.signals import post_syncdb
from django.dispatch import receiver

from server_talk.scheduler import register_interval_job
from server_talk import models as server_talk_model
from server_talk.tasks import heartbeat_check, inventory_hash_check
from server_talk.conf.settings import (HEARTBEAT_QUERY_INTERVAL,
    INVENTORY_QUERY_INTERVAL)
from server_talk.models import LocalNode

logger = logging.getLogger(__name__)


@receiver(post_syncdb, dispatch_uid='create_identify', sender=server_talk_model)
def create_identify(sender, **kwargs):
    print 'Creating local node identity ...'
    info, created = LocalNode.objects.get_or_create(lock_id='1', defaults={'uuid': unicode(uuid.uuid4())})
    if not created:
        print 'Existing identify not modified.'


register_interval_job('heartbeat_check', heartbeat_check, seconds=HEARTBEAT_QUERY_INTERVAL)
register_interval_job('inventory_hash_check', inventory_hash_check, seconds=INVENTORY_QUERY_INTERVAL)

