from django.contrib import admin

from queue_manager.models import Queue, QueueItem


class QueueItemInline(admin.StackedInline):
    model = QueueItem


class QueueAdmin(admin.ModelAdmin):
    model = Queue
    inlines = [QueueItemInline]


admin.site.register(Queue, QueueAdmin)
