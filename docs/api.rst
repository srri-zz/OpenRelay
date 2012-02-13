=============
API reference
=============

**OpenRelay node protocol V0.1**

=== =========
URL View name
=== =========
services/announce/ service-announce
=== =========


# ping: request a pong from another server and stores the delay in weighted running average for the server
# contacts: requests a list of servers from another server
# inventory: requests a list of resources
# proxy: relays an Http request to another server
# request-resource: request a resource from another server
# my_name_is: request server info (version, api version)
# workaholic: requests the cpu load and resource serving stats of a server (could be merged with [ping])
# report: blacklist a server that has repeatedly tampered with files (from authoritative nodes only)
# unblacklist
