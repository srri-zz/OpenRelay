from django.conf import settings

PORT = getattr(settings, 'SERVER_PORT', 8000)
