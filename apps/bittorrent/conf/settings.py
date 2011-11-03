from django.conf import settings

OUTPUT_DIR = getattr(settings, 'BITTORRENT_OUTPUT_DIR', '/tmp')
LISTEN_PORT = getattr(settings, 'BITTORRENT_LISTEN_PORT', 6881)
ENABLE_DHT = getattr(settings, 'BITTORRENT_ENABLE_DHT', True)
