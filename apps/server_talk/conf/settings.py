import socket

from django.conf import settings

PORT = getattr(settings, 'SERVER_PORT', 8000)
IPADDRESS = getattr(settings, 'SERVER_IPADDRESS', socket.gethostbyname(socket.gethostname()))
HEARTBEAT_QUERY_INTERVAL = getattr(settings, 'SERVER_HEARTBEAT_QUERY_INTERVAL', 10)
INVENTORY_QUERY_INTERVAL = getattr(settings, 'SERVER_INVENTORY_QUERY_INTERVAL', 30)
SIBLINGS_QUERY_INTERVAL = getattr(settings, 'SERVER_SIBLINGS_QUERY_INTERVAL', 30)
HEARTBEAT_FAILURE_THRESHOLD = getattr(settings, 'SERVER_HEARTBEAT_FAILURE_THRESHOLD', 30)
