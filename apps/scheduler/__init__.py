from __future__ import absolute_import

import logging

from django.db.models.signals import post_syncdb
from django.dispatch import receiver

from signaler.signals import pre_collectstatic

from .api import register_interval_job, AlreadyScheduled
from .runtime import backend_scheduler

logger = logging.getLogger(__name__)


@receiver(post_syncdb, dispatch_uid='scheduler_shutdown_post_syncdb')
def scheduler_shutdown_post_syncdb(sender, **kwargs):
    logger.debug('Scheduler shut down on post syncdb signal')
    backend_scheduler.shutdown()


@receiver(pre_collectstatic, dispatch_uid='sheduler_shutdown_pre_collectstatic')
def sheduler_shutdown_pre_collectstatic(sender, **kwargs):
    logger.debug('Scheduler shut down on collectstatic signal')
    backend_scheduler.shutdown()
