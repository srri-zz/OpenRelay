.. |done| image:: _static/tick_circle.png
.. |started| image:: _static/arrow_circle_double.png

================
Planned features
================

Node availability
-----------------
* Node based routing

  * Give nodes the oportunity to receive and forward API messages when behind routers

* HTTP Proxy support

  * Give nodes the ability to act as gateways between the OpenRelay network and the regular internet 

* Load balancing

  * Node take into account the CPU load of other nodes when issuing requests
  
* Throttling support


Security
--------
* Inter node communication encryption

  * Avoid eavesdropping of node communication

* Validated API calls |done|

  * Avoid tampering with the node messages

* Hidden node support

  * Nodes don't announce their presence and only interact with the network via another node acting as gateway

* Resource size detection

  * Prevent DoS attack by rogue nodes lying about file sizes
  
* Authoritative node support

  * Node blacklisting
  
    * Rogue, hacked nodes
  
  * Content blacklisting
  
    * Ability to take down improper contents such as child pornography

* Public key replication

  * Remove dependancy on external keyservers


Usability
---------
* Zip file upload support |done|

  * Add the ability to upload entire websites in one step

* Unreplicabale resources

  * To support services like chat or web apps
  
* Search and distributed content indexing |started|

  * Provide full text search capabilities for all content in the OpenRelay network
  

Content availability
--------------------
* ARP-like resource locating algorithm

  * For used as a last resort when a resource hasn't been indexed

* Content seeding

  * Improve the speed at which new resources are cached by the network

* Unperishable content

  * Support for resources that should not be deleted even when not in demand


Optimization
------------
* More caching improvements

  * Faster content display, improve user experience

* Implement timeouts for the API calls |done|


Legend
~~~~~~
* |done| - Done
* |started| - Started
