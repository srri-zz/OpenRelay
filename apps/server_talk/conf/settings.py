from django.conf import settings

PORT = getattr(settings, 'SERVER_PORT', 8000)
HEARTBEAT_QUERY_INTERVAL = getattr(settings, 'SERVER_HEARTBEAT_QUERY_INTERVAL', 10)
