OpenRelay
=============

OpenRelay is a p2p (peer to peer) based web hosting solution. It takes 
advantage of Bittorrent to send files between the hosts as well as 
Dynamic DNS for updating nodes. 

License
-------
OpenRelay is licensed under the GNU GPL v3 (See LICENSE file)

Learn More
----------
http://peer.to/peer

Installation
------------

Initialize a ``virtualenv`` to deploy the project:

    $ virtualenv --no-site-packages OpenRelay

Or clone the latest development version straight from github:

    $ cd OpenRelay
    $ git clone git://github.com/Captainkrtek/OpenRelay.git

To install the python dependencies ``easy_install`` can be used, however for easier retrieval a production dependencies file is included, to use it execute:

    $ source bin/activate
    $ cd OpenRelay
    $ pip install -r requirements/production.txt
    $ git submodule init
    $ git submodule update

Populate the database with the project's schema doing:

    $ ./manage.py syncdb 
    
Launch the server daemon doing:

    $ ./runserver.sh start
    
Open a browser and point it to http:127.0.0.1:8000

To stop the server daemon process do:

    $ ./runserver.sh stop
