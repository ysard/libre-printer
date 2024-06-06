.. _configuration_examples:

**********************
Configuration examples
**********************

You will find here some simple but common examples of configuration for the
``libreprinter.conf`` file in various printer use cases.

Note: Keep in mind that for Epson processing you may also want to modify the
configuration of your ``convert-escp2`` binary taken from the RetroPrinter project,
like the number of pins (``./config/epson_pins``),
the page size (``./config/page_size``), the font (``./config/epson_font``),
the charset (``./config/charset``) or the margins (``./config/default_margins``).

- A Simple Epson 9 pins Serial printer

  This printer sends ESCP2 commands and you want PDF files.

  .. code-block::

    [misc]
    emulation=epson

    [serial_printer]
    enabled=yes

  Note: For serial interface tuning like flow control or logic
  levels, see the section ``[serial_printer]`` of the config file.


- If you just want the text files without ESCP2 commands in it

  .. code-block::

    [misc]
    emulation=epson
    endlesstext=strip-escp2-jobs

    [serial_printer]
    enabled=yes

  Note: A PDF will be also created


- A serial printer that sends basic text

  .. code-block::

    [misc]
    emulation=text

    [serial_printer]
    enabled=yes


- A serial printer that sends basic text indefinitely in a stream

  .. code-block::

    [misc]
    emulation=text
    endlesstext=plain-stream

    [serial_printer]
    enabled=yes


- A parallel Epson ESCP2 printer

  .. code-block::

    [misc]
    emulation=epson

    [serial_printer]
    enabled=no


- A parallel HP PCL printer

  .. code-block::

    [misc]
    emulation=hp

    [serial_printer]
    enabled=no
