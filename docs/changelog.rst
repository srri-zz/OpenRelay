=========
Changelog
=========

Version 0.4
-----------
* Node list sharing - Nodes now share their known node list with others,
  this make the network interconnections grown faster.
* Communication between nodes is now signed by the originator and
  verified by the recipient, this improves security by allowing tamper 
  detection of the inter node messages.


Version 0.3
-----------
* More control over the key creation parameters
* Queue manager app backported from Mayan EDMS to improve background tasks
  efficiency
* Slash '/' character can now be part of a resources name in effect
  allowing filesystem path emulation
* The ammount of technical details shown to the user has been replaced
  with informative views
* Improved node indentity by using a private and public per node
* Better key handling, key publishing view and background key generation
* New configuration option: SERVER_HEARTBEAT_FAILURE_THRESHOLD, to
  determine when to delete a node from the siblings list
* Better remote node status detection and reporting
* Interactive locale switching
* Translation: Spanish, Czech, Klingon and Ukrainian
* Better caching of remote resources information
* Refactoring of the entire API
* Resource model class refactoring
* Project wide improved error and exception handling
* Filesystem storage improvements (deletion, filename sanitation)
* Adding of contact information to the about template, cleaned up the markup
* Improvements in template appearance (base, about, home and forms, image 
  centering, etc)
* Favicon added
* New SERVER_INVENTORY_QUERY_INTERVAL configuration option to setup
  the time interval between nodes inventory query API call
* Node resource sharing API call implemented
* Node resource inventory sharing API call implemented
* Node resource inventory hash sharing API call implemented
* Updated the default keyserver of the project to just 'peer.to'
* Documentation updates, added development, installation, internals,
  license and settings pages
* New SERVER_HEARTBEAT_QUERY_INTERVAL configuration options to enable
  the setting of the heartbeat query interval
* CPU load calculator for the heartbeat API call
* lock_manager app from Mayan EDMS to avoid race conditions in scheduled
  task execution
* Added background scheduled tasks support using APScheduler
