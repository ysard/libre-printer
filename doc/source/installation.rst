.. _installation:

Installation
============

Foreword
--------

Language used
~~~~~~~~~~~~~

All the main code is developped in Python3.6+ language.

However external programs like ESC converters are written in C or C++.
This is the choice of the programmers depending on their preferences or by desire to
hide their work and make their project not modifiable (ex: the binaries of Retroprinter).


System requirements
-------------------

A functional Python3 environment must be installed on your computer.

For the eventual compilation of external binaries, you may need a GCC/G++ based build chain.

**Most/all of these requirements are already installed on basic GNU/Linux systems.**


.. _setting_up_a_virtual_environment:

Setting up a virtual environment for the development
----------------------------------------------------

As always, the use of a Python virtual environment
(via `virtualenvwrapper <https://docs.python-guide.org/dev/virtualenvs/>`_) is **strongly advised**
at least for development purposes.

This is not a mandatory step but it is a good and a **simple** practice to separate projects
from each other in order to avoid conflicts between dependencies.

* Install virtualenvwrapper:

.. code-block:: bash

   $ pip install --user virtualenvwrapper

* Edit your ``~/.bashrc`` or ``~/.zshrc`` file to source the ``virtualenvwrapper.sh`` script with these lines:

.. code-block:: bash

   $ export PATH=$PATH:~/.local/bin
   $ export WORKON_HOME=~/.virtualenvs
   $ mkdir -p $WORKON_HOME
   $ # The location of this script may vary depending on your GNU/Linux distro
   $ # and depending of your installation procedure with pip.
   $ # See ~/.local/bin/ or /usr/bin
   $ source ~/.local/bin/virtualenvwrapper.sh

* Restart your terminal or run:

.. code-block:: bash

   $ source ~/.bashrc

* Create your virtualenv:

.. code-block:: bash

   $ mkvirtualenv libre-printer -p /usr/bin/python3

* Later, if you want to work in the virtualenv:

.. code-block:: bash

   $ workon libre-printer


Install the released version
----------------------------

|project_name| package is available on PyPI (Python Package Index), the official third-party
software repository for Python language:
`LibrePrinter service <https://pypi.python.org/pypi/libre-printer>`_.

You can install it with the following command on all systems with a Python environment with ``pip``:

.. code-block:: bash

   $ pip install libre-printer

.. note:: Don't forget to add the flag ``--user`` to the command above if you don't use
   virtual environment or if you do not have root privileges on your system.


At this point a new command is available in your shell to launch the service:

.. code-block:: bash

    $ libre-printer


.. _install_dev_version:

Install the development version
-------------------------------

Install from sources
~~~~~~~~~~~~~~~~~~~~

If you have Git installed on your system, it is also possible to install the development
version of |project_name|.

Before installing the development version, you may need to uninstall the standard version
of |project_name| using ``pip``:

.. code-block:: bash

   $ pip uninstall libre-printer

Then do:

.. code-block:: bash

   $ git clone https://github.com/ysard/libre-printer
   $ cd libre-printer
   $ make dev_install


The ``make dev_install`` command uses ``pip install -e .[dev]`` command which allows
you to follow the development branch as it changes by creating links in the right places
and installing the command line scripts to the appropriate locations.

Moreover, it installs packages listed in the dev section of ``extras_require`` in
``setup.py/setup.cfg``, in addition to any normal dependencies as necessary.

Please note that your changes in the code are directly usable without having to reinstall the package.

Then, if you want to update |project_name| at any time, in the same directory do:

.. code-block:: bash

   $ git pull


Uninstall
~~~~~~~~~

Just do:

.. code-block:: bash

   $ make uninstall


Testing
~~~~~~~

|project_name| uses the Python `pytest <https://pytest.org/>`_ testing package.

You can test the packages from the source directory with:

.. code-block:: bash

   $ make tests
