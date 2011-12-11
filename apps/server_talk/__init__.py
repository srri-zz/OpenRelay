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
from server_talk.literals import DEFAULT_PASSPHRASE

logger = logging.getLogger(__name__)


@receiver(post_syncdb, dispatch_uid='create_identify', sender=server_talk_model)
def create_identify(sender, **kwargs):
    node = LocalNode()
    if not node.uuid:
        print 'Creating local node identity ...'
        if kwargs['interactive']:
            name_real = raw_input('Enter a name to describe this node: ')
            name_email = raw_input('Enter an e-mail associated with this node: ') or name_real
            name_comment = raw_input('Enter comment for this node: ') or name_real
            while True:
                passphrase = raw_input('Enter a passphrase to lock this key (or just press Enter for none): ')
                if not passphrase:
                    passphrase_verify = passphrase
                    break
                passphrase_verify = raw_input('Enter again the same passphrase to verify: ')
                if passphrase == passphrase_verify:
                    break
                else:
                    print '\nPassphrases do not match, try again.\n'
                if not passphrase:
                    passphrase = None
        else:
            name_real = 'Anonymous'
            print 'Using %s as the node name' % name_real
            name_email = name_real
            name_comment = name_real
            passphrase = None
            # TODO: generate random passphrase
            # TODO: save random passphrase in settings_local file

        # TODO: fix, python-gpg is not signing data with non passphrase
        # keys, assign a predicatable passphare as a default
        # TODO: investigate the python-gpg source code
        if not passphrase:
            logger.debug('blank passphrase found, replacing with default')
            passphrase = DEFAULT_PASSPHRASE
            
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

