from django.db import models


class ResourceManager(models.Manager):
    def get(self, *args, **kwargs):
        try:
            return super(ResourceManager, self).get(*args, **kwargs)
        except self.model.MultipleObjectsReturned:
            uuid = kwargs.pop('uuid')
            return super(ResourceManager, self).get_query_set().filter(uuid=uuid).order_by('-time_stamp')[0]
