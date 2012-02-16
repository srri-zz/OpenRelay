# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'LocalNodeModel'
        db.create_table('server_talk_localnodemodel', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=48)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('email', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('lock_id', self.gf('django.db.models.fields.CharField')(default='1', unique=True, max_length=1)),
        ))
        db.send_create_signal('server_talk', ['LocalNodeModel'])

        # Adding model 'Sibling'
        db.create_table('server_talk_sibling', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=48)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('email', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('ip_address', self.gf('django.db.models.fields.IPAddressField')(max_length=15)),
            ('port', self.gf('django.db.models.fields.PositiveIntegerField')(blank=True)),
            ('last_heartbeat', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2012, 2, 16, 0, 50, 56, 553452), blank=True)),
            ('cpuload', self.gf('django.db.models.fields.PositiveIntegerField')(default=0, blank=True)),
            ('status', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('failure_count', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('last_inventory_hash', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2012, 2, 16, 0, 50, 56, 553542), blank=True)),
            ('inventory_hash', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('last_siblings_hash', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime(2012, 2, 16, 0, 50, 56, 553587), blank=True)),
            ('siblings_hash', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
        ))
        db.send_create_signal('server_talk', ['Sibling'])

        # Adding model 'NetworkResourceVersion'
        db.create_table('server_talk_networkresourceversion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=48, blank=True)),
            ('timestamp', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('metadata', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('signature_properties', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('server_talk', ['NetworkResourceVersion'])

        # Adding model 'ResourceHolder'
        db.create_table('server_talk_resourceholder', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('resource_version', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['server_talk.NetworkResourceVersion'])),
            ('node', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['server_talk.Sibling'])),
        ))
        db.send_create_signal('server_talk', ['ResourceHolder'])


    def backwards(self, orm):
        
        # Deleting model 'LocalNodeModel'
        db.delete_table('server_talk_localnodemodel')

        # Deleting model 'Sibling'
        db.delete_table('server_talk_sibling')

        # Deleting model 'NetworkResourceVersion'
        db.delete_table('server_talk_networkresourceversion')

        # Deleting model 'ResourceHolder'
        db.delete_table('server_talk_resourceholder')


    models = {
        'server_talk.localnodemodel': {
            'Meta': {'object_name': 'LocalNodeModel'},
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'lock_id': ('django.db.models.fields.CharField', [], {'default': "'1'", 'unique': 'True', 'max_length': '1'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '48'})
        },
        'server_talk.networkresourceversion': {
            'Meta': {'object_name': 'NetworkResourceVersion'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'metadata': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'signature_properties': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'timestamp': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '48', 'blank': 'True'})
        },
        'server_talk.resourceholder': {
            'Meta': {'object_name': 'ResourceHolder'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'node': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['server_talk.Sibling']"}),
            'resource_version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['server_talk.NetworkResourceVersion']"})
        },
        'server_talk.sibling': {
            'Meta': {'object_name': 'Sibling'},
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'cpuload': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0', 'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'failure_count': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'inventory_hash': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'ip_address': ('django.db.models.fields.IPAddressField', [], {'max_length': '15'}),
            'last_heartbeat': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 16, 0, 50, 56, 553452)', 'blank': 'True'}),
            'last_inventory_hash': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 16, 0, 50, 56, 553542)', 'blank': 'True'}),
            'last_siblings_hash': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2012, 2, 16, 0, 50, 56, 553587)', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'port': ('django.db.models.fields.PositiveIntegerField', [], {'blank': 'True'}),
            'siblings_hash': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'status': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '48'})
        }
    }

    complete_apps = ['server_talk']
