.. _working_with_source_code:

Working with LibrePrinter source code
=====================================

All the main code is developped in Python3.6+ language.

However external programs like ESC converters are written in C or C++.
This is the choice of the programmers depending on their preferences or by desire to
hide their work and make their project not modifiable (ex: the binaries of Retroprinter).

..
    The extension is compiled during installation or directly downloaded without compiling if your
    system supports **Python wheels**.
    This is a *relatively new standard* for the distribution of Python packages
    available for Linux, Windows or macOS with ``pip >= 1.4`` and ``setuptools >= 0.8``.
    This system is a faster and secure way to install native C extension packages.

    .. seealso:: `https://pythonwheels.com/ <https://pythonwheels.com/>`_


.. note::
   All Python modules are documented with a rate of 100%.
   Code is also heavily tested with a coverage rate of at least 90%.


Technical documentation
=======================

.. toctree::
   :maxdepth: 5

   converters_doc
   watchdogs_doc
   core_doc
