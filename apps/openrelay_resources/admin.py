from django.contrib import admin

from resources.models import Resource


class ResourceAdmin(admin.ModelAdmin):
    model = Resource
    #list_display = ('user', 'document', 'datetime_accessed')
    #readonly_fields = ('user', 'document', 'datetime_accessed')
    #list_filter = ('user',)
    #date_hierarchy = 'datetime_accessed'


admin.site.register(Resource, ResourceAdmin)
