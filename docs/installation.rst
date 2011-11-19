============
Installation
============

Initialize an ``virtualenv`` to deploy the project::

    $ virtualenv --no-site-packages OpenRelay

Or clone the latest development version straight from github::

    $ cd OpenRelay
    $ git clone git://github.com/Captainkrtek/OpenRelay.git

To install the python dependencies using the production dependencies file included::

    $ source bin/activate
    $ cd OpenRelay
    $ pip install -r requirements/production.txt
    $ git submodule init
    $ git submodule update

Populate the database with the project's schema doing::

    $ ./manage.py syncdb 
    
Launch the server daemon doing::

    $ ./runserver.sh start
    
Open a browser and point it to http:127.0.0.1:8000

To stop the server daemon process do::

    $ ./runserver.sh stop
