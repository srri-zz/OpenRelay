=============
API reference
=============

**OpenRelay protocol specification V0**

service-announce
----------------

**URL**: services/announce/

Announces a new node to an established node, for initial seeding in the
OpenRelay network.  Returns the established node's information if the new
node's key verification is successful.

**Returns**::

  {
    'ip_address': <established node IP address>,
    'port': <established node IP port>,
  }

service-heartbeat
-----------------

**URL**: services/heartbeat/

Ask a node for it's current CPU usage.

**Returns**::

  {
    'cpuload': str(<sibling node CPU usage>)
  }


service-inventory_hash
----------------------

**URL**: service/inventory/hash

Ask a node for it's resource inventory hash, to avoid retrieving the
entire resource list on every call.

**Return**::

  {
    'inventory_hash': <resource inventory hash>
  }


service-siblings_hash
---------------------

**URL**: service/siblings/hash

Ask a node for it's node list hash, to avoid retrieving the
entire node list on every call.

**Return**::

  {
    'siblings_hash': <sibling node node inventory hash>
  }

resource_file
-------------

**URL**: resources/resource_file/<uuid>/


version-download
----------------

URL: resources/version/download/<uuid>/


version-serve
-------------

URL: resources/version/serve/<uuid>/


version
-------

URL: resources/version/<uuid>/

version-root
------------

URL: resources/version/


sibling-root
------------

URL: resources/sibling/
