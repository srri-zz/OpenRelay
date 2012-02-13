from __future__ import absolute_import
import logging

from django.db.models.signals import post_syncdb
from django.dispatch import receiver

from .api import register_interval_job, AlreadyScheduled
from .runtime import scheduler

logger = logging.getLogger(__name__)


@receiver(post_syncdb, dispatch_uid='scheduler_shutdown_post_syncdb')
def scheduler_shutdown_post_syncdb(sender, **kwargs):
    logger.debug('Scheduler shut down on post syncdb signal')
    scheduler.shutdown()
