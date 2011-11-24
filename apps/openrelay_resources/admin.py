from django.contrib import admin

from openrelay_resources.models import Resource, Version


class VersionInline(admin.StackedInline):
    model = Version


class ResourceAdmin(admin.ModelAdmin):
    model = Resource
    inlines = [VersionInline]


admin.site.register(Resource, ResourceAdmin)
