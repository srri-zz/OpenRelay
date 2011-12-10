import logging

from django.db.models.signals import post_syncdb
from django.dispatch import receiver

from scheduler import register_interval_job
from core.runtime import gpg

from server_talk import models as server_talk_model
from server_talk.tasks import heartbeat_check, inventory_hash_check, siblings_hash_check
from server_talk.conf.settings import (HEARTBEAT_QUERY_INTERVAL,
    INVENTORY_QUERY_INTERVAL, SIBLINGS_QUERY_INTERVAL)
from server_talk.models import LocalNode
from server_talk.api import NetworkCall

logger = logging.getLogger(__name__)


@receiver(post_syncdb, dispatch_uid='create_identify', sender=server_talk_model)
def create_identify(sender, **kwargs):
    node, created = LocalNode.objects.get_or_create(lock_id='1')
    if created or not node.uuid:
        print 'Creating local node identity ...'
        name_real = raw_input('Enter a name to describe this node: ')
        name_email = raw_input('Enter an e-mail associated with this node: ')
        name_comment = raw_input('Enter comment for this node: ')
        while True:
            passphrase = raw_input('Enter a passphrase to lock this key: ')
            passphrase_verify = raw_input('Enter again the same passphrase to verify: ')
            if passphrase == passphrase_verify:
                break
            else:
                print '\nPassphrases do not match, try again.\n'
        key_args = {
            'name_real': name_real,
            'name_email': name_email,
            'name_comment': name_comment,
            'passphrase': passphrase,
            'key_type': 'RSA',
            'key_length': 2048,
            'subkey_type': 'RSA',
            'subkey_length': 2048,
            'expire_date': 0,
        }
        print 'Creating node key, type on the keyboard, move the mouse, utilize the disks to generate entropy.'
        try:
            key = gpg.create_key(**key_args)
            node.uuid = key.fingerprint
            node.name = name_real
            node.email = name_email
            node.comment = name_comment
            node.save()
            network = NetworkCall()
            network.publish_key(key)
        except Exception, msg:
            print 'Unhandled exception: %s' % msg
    else:
        print 'Existing identity not modified.'


register_interval_job('heartbeat_check', heartbeat_check, seconds=HEARTBEAT_QUERY_INTERVAL)
register_interval_job('inventory_hash_check', inventory_hash_check, seconds=INVENTORY_QUERY_INTERVAL)
register_interval_job('siblings_hash_check', siblings_hash_check, seconds=SIBLINGS_QUERY_INTERVAL)

