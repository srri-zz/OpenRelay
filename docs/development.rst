.. _development:

Development
===========

**OpenRelay** is under active development, and contributions are welcome.

.. _scm:

--------------
Source Control
--------------
The **OpenRelay** source is managed with Git_

The project is publicly accessible, hosted and can be cloned from **GitHub** using::

    $ git clone git://github.com/Captainkrtek/OpenRelay.git


Git branch structure
--------------------

**OpenRelay** follows the model layout by Vincent Driessen in his `Successful Git Branching Model`_ blog post. Git-flow_ is a great tool for managing the repository in this way.

``development``
    The "next release" branch, likely unstable.
``master``
    Current production release (|version|).
``feature/``
    Unfinished/ummerged feature.


Each release is tagged and available for download on the Downloads_ section of the **OpenRelay** repository on GitHub_.

When submitting patches, please place your feature/change in its own branch prior to opening a pull request on GitHub_.
To familiarize yourself with the technical details of the project read the :ref:`internals` section.

.. _GitHub: https://www.github.com
.. _Git: http://git-scm.org
.. _`Successful Git Branching Model`: http://nvie.com/posts/a-successful-git-branching-model/
.. _git-flow: http://github.com/nvie/gitflow
.. _Downloads:  https://github.com/Captainkrtek/OpenRelay/downloads

.. _docs:

----------------
Getting Involved
----------------

**OpenRelay**, as mentioned earlier, is under active development. If you're interested in getting involved, clone the repo and send us a pull request with your update. If you're interested
in becoming a maintainer, email steve@peer.to with your qualifications.

-----------------
Documentation
-----------------

The documentation is written in `reStructured Text`_ format.

The documentation lives in the ``docs`` directory.  In order to build it, you will first need to install Sphinx_. ::

	$ pip install sphinx


Then, to build an HTML version of the documentation, simply run the following from the **docs** directory::

	$ make html

Your ``docs/_build/html`` directory will then contain an HTML version of the documentation, ready for publication on most web servers.

You can also generate the documentation in format other than HTML.

.. _`reStructured Text`: http://docutils.sourceforge.net/rst.html
.. _Sphinx: http://sphinx.pocoo.org

