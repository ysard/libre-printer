Contributing
============

Here you will find how to contribute to the project, setting up an environment,
submit modifications & report bugs.

.. contents:: Summary
    :depth: 2
    :local:
    :backlinks: top

Setting up the local copy of the code
-------------------------------------

1. If you are a new contributor, you will have to fork the repository
   (`https://github.com/ysard/libre-printer <https://github.com/ysard/libre-printer>`_), clone it,
   and then add an upstream repository.

   More information on: `GitHub doc: forking workflow <https://docs.github.com/en/get-started/quickstart/fork-a-repo>`_.

   .. note::
      Please note that the active branch of development is named ``dev``.
      The ``master`` branch is the stable release branch; please avoid proposing pull-requests on this branch except for bugfixes.


   .. code-block:: bash

      $ # Clone your fork
      $ git clone -b dev git@github.com:<your_username>/libre-printer.git
      $ # Add upstream repository
      $ git remote add upstream git@github.com:ysard/libre-printer.git


   Now, you should have 2 remote repositories named (``git branch``):

   - upstream, which refers to the |project_name| repository
   - origin, which refers to your personal fork

.. new line

2. Develop your contribution:

   Pull the latest changes from upstream:

   .. code-block:: bash

      $ git checkout <branch_of_reference>
      $ git pull upstream <branch_of_reference>

   Create a branch for the feature you want to work on; the branch name should be explicit and if possible related to an
   opened issue (Ex: Issue number *000* in the following).

   .. code-block:: bash

      $ git checkout -b bugfix-#000

   **Make small commits with explicit messages about why you do things as you progress**
   (``git add`` and ``git commit``).

   **Cover your code with unit tests and run them before submitting your contribution.**

   The following Make command is here to run all the tests & coverage stats:

   .. code-block:: bash

      $ make coverage

.. new line

3. Submit your contribution:

   Push your changes to your fork:

   .. code-block:: bash

      $ git push origin bugfix-#000

   Go to the GitHub website. The new branch and a green pull-request button should appear.
   To facilitate reviewing and approval, it is strongly encouraged to add a full description of
   your changes to the pull-request.


Setting up the build environment
--------------------------------

Once you’ve cloned your fork of the |project_name| repository, you should set up
a Python development environment tailored for the project.

See the chapter :ref:`setting_up_a_virtual_environment` of the installation process.

Then see the chapter :ref:`install_dev_version`.


Documentation
-------------

Documentation is built using `Sphinx <http://sphinx-doc.org/>`_.

..
    and hosted `xxx <xxx>`_.

Documentation is mostly written as `reStructuredText <http://www.sphinx-doc.org/en/master/usage/restructuredtext/index.html>`_
(.rst) files.

reStructuredText enables python-generated text to fill your documentation as in the auto-importing
of modules or usage of plugins like `sphinx-argparse`.


Here's a subset of reStructuredText to help you get started writing these files:

- `Full specification <https://docutils.sourceforge.io/docs/ref/rst/restructuredtext.html>`_
- `Quick references for Sphinx <https://thomas-cokelaer.info/tutorials/sphinx/rest_syntax.html>`_

..
    Human-readable command-line documentation is written using a Sphinx extension called
    `sphinx-argparse <https://sphinx-argparse.readthedocs.io/en/latest/index.html>`_.


Folder structure
~~~~~~~~~~~~~~~~

The documentation source-files are located in ``./doc/source/``, with ``./doc/source/index.rst`` being the main entry point.
Each subsection of the documentation is a ``.rst`` file inside ``./doc/source/``.

Html files are generated in ``./doc/build/``.


Building documentation
~~~~~~~~~~~~~~~~~~~~~~

Building the documentation locally is useful to test changes.
First, make sure you have the development dependencies installed; See `Setting up the build environment`_

Then build the HTML output format by running:

.. code-block:: bash

    make doc
    # or
    make -C ./doc html


Sphinx caches built documentation by default, which is generally great, but can cause the sidebar
of pages to be stale. You can clean out the cache with:

.. code-block:: bash

    make -C ./doc clean


Reporting bugs
--------------

Please `report bugs on GitHub <https://github.com/ysard/libre-printer/issues>`_.


Test the project
----------------

The project frequently uses tricks to simulate the behavior of
the hardware interface without having it on hand. This allows for
many tests to be executed quickly and independently of the hardware.

For this purpose, unit tests use a virtual serial interface
initialized with the socat tool.

It is also possible to run the service with a virtual interface during
manual tests.

- The following command will create a virtual interface named ``virtual-tty`` in the project directory:

.. code-block:: bash

   $ make test_tty_to_tty

- Configure the path to the virtual interface via the ``serial_port=``
  parameter in the ``libreprinter.conf`` file.

- Start the service:

.. code-block:: bash

   $ make run

- Once launched, the service awaits an acknowledgment from the interface.
  This is something you can simulate with the following command:

.. code-block:: bash

   $ make send_end_config

- Then send the data as a computer does to a printer,
  use the ``input_tty_generator.py`` script located in ``tools/``:

.. code-block:: bash

   $ ./input_tty_generator.py
