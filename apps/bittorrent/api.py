from twisted.python import log

from bittorrent.BTApp import BTApp, BTConfig
from bittorrent.conf.settings import OUTPUT_DIR
from bittorrent.conf.settings import LISTEN_PORT
from bittorrent.conf.settings import ENABLE_DHT


def fetch_torrent(torrent_file):
    app = BTApp(
        save_dir=OUTPUT_DIR,
        listen_port=LISTEN_PORT,
        enable_DHT=ENABLE_DHT,
        remote_debugging=False
    )

    try:
        log.msg('Adding: {0}'.format(torrent_file))
        config = BTConfig(torrent_file)
        config.downloadList = None
        app.add_torrent(config)
    except:
        log.err()
        log.err("Failed to add {0}".format(torrent_file))

    app.start_reactor()
