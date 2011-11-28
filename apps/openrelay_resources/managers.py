from django.db import models

from openrelay_resources.literals import TIMESTAMP_SEPARATOR


class ResourceManager(models.Manager):
    def get(self, *args, **kwargs):
        try:
            uuid, timestamp = kwargs.get('uuid', '').split(TIMESTAMP_SEPARATOR)
            # TODO: Include *args, **kwargs in one of both of these queries?
            resource = super(ResourceManager, self).get(uuid=uuid)
            return resource.version_set.get(timestamp=timestamp)
        except ValueError:
            try:
                return super(ResourceManager, self).get(*args, **kwargs)
            except self.model.MultipleObjectsReturned:
                # The database is screwed up!!
                raise
