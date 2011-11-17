========
Settings
========

Resources
---------

.. data:: RESOURCES_STORAGE_BACKEND

    Default: ``FileBasedStorage`` class

    As Django supports file storage abstraction, adminitrators of nodes could choose instead to use other storage means such as NAS, SANs, Cloud based (S3), FTP, Samba, etc.



.. data:: RESOURCES_FILESTORAGE_LOCATION

    Default: ``resource_storage``

    This setting relates exclusively to the FileBaseStorage class and detemines where in the physical disk are the node files going to be stored.


Core
----

.. data:: CORE_KEYSERVERS

    Default: ``['http://peer.to:11371']``
    
    The list of key server that the node will query for public keys to verify resources.  This setting option may be eliminated in the future when OpenRelay supports storing and replicating of public keys without using centralize key servers.


API
---

.. data:: SERVER_PORT

    Default: ``8000``
    
    TCP/IP port where the UI and API can be accessed.


.. data:: SERVER_HEARTBEAT_QUERY_INTERVAL

    Default: ``10``
    
    
    Time interval in seconds to perform heartbeat checks on other OpenRelay nodes.


.. data:: SERVER_INVENTORY_QUERY_INTERVAL

    Default: ``11``
    
    
    Time interval in seconds to perform an inventory hash checks on other OpenRelay nodes.
