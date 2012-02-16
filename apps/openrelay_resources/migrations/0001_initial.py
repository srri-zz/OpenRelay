# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Resource'
        db.create_table('openrelay_resources_resource', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('uuid', self.gf('django.db.models.fields.CharField')(max_length=48, blank=True)),
        ))
        db.send_create_signal('openrelay_resources', ['Resource'])

        # Adding model 'Version'
        db.create_table('openrelay_resources_version', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('timestamp', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('resource', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['openrelay_resources.Resource'])),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('last_access', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('openrelay_resources', ['Version'])


    def backwards(self, orm):
        
        # Deleting model 'Resource'
        db.delete_table('openrelay_resources_resource')

        # Deleting model 'Version'
        db.delete_table('openrelay_resources_version')


    models = {
        'openrelay_resources.resource': {
            'Meta': {'object_name': 'Resource'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'uuid': ('django.db.models.fields.CharField', [], {'max_length': '48', 'blank': 'True'})
        },
        'openrelay_resources.version': {
            'Meta': {'ordering': "('-timestamp',)", 'object_name': 'Version'},
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_access': ('django.db.models.fields.DateTimeField', [], {}),
            'resource': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['openrelay_resources.Resource']"}),
            'timestamp': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        }
    }

    complete_apps = ['openrelay_resources']
