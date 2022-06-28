.. _service_configuration:

*********************
Service configuration
*********************

As it was mentioned in the project presentation chapter (:ref:`project_structure`),
|project_name| relies on a service that manages the data coming from the interface.

The behavior of this service is configurable in a single file centralizing
commands that are considered useful for the RetroPrinter project.

Please note that the configuration of the ESC/P2 converter is always done through
separate files files identical to the original project.
Although this is noted on the list of things to fix one day.


The configuration file is `libreprinter.conf`.
It is currently split into 3 sections:

- `misc` (miscellaneous settings): Settings that apply to the whole service;
  Defines folders, paths to conversion binaries, type of protocol to decode, etc.

- `parallel_printer`: Interface configuration parameters in case a printer using
  the Parallel/Centronics standard is connected.
  This is the default setting.

- `serial_printer`: Interface configuration parameters in case a printer using the
  Serial/RS-232 standard is connected.
  This situation is disabled by default.

.. contents:: Summary
    :depth: 2
    :local:
    :backlinks: top

[misc]
======

- **start_cleanup=no**

    Reset directories in output_path, and shared memory during startup.

- **escp2_converter_path=**

    Path of espc2 converter. If the binary is not included in the path its expected
    name is "convert-escp2".

- **pcl_converter_path=**

    Path of the GhostPCL binary used to convert HP PCL files with ghostscript

- **endlesstext=no**

    Equivalent of simple_spool legacy config.
    Possible values & behaviors:

    ======================= =======================================
    **plain-stream**        text stream
    **strip-escp2-stream**  remove escp2 commands stream
    **plain-jobs**          text job
    **strip-escp2-jobs**    remove escp2 commands job
    **no**                  waits for the pages one after the other
    ======================= =======================================

    If `plain-stream` or `strip-escp2-stream`, output_printer option will be disabled.

- **line_ending=unix**

    Used to convert line endings in plain-stream/plain-jobs conversion modes;
    equivalent of linefeed_ending legacy config.
    Possible values: unix/windows

- **usb_passthrough=no**

    Raw peripheral path. If different from "no", data will be stored in raw files
    and then directly written on this peripheral (which will be considered as a
    file opened in write mode) without further processing.
    Possible values: "no" or any path even a printer path like "/dev/usb/lp0".

    WARNING: In this last example be warned that output_printer setting is *NOT*
    disabled. It should be noted that any "raw" parallel interface like `/dev/usb/lpx`
    disappears when Cups is used on it. Thus it can't be used with this
    functionality anymore.
    TL;DR: Do not use the path of a printer whose name you have entered in
    `output_printer`.

- **output_printer=no**

    Cups printer name. If different of "no", put the name of a printer installed
    and configured in Cups. The list of printers is given by the command "lpstat -p -d".
    Data will be converted in pdf and redirected to the printer.

- **serial_port=/dev/ttyACM0**

    Serial port on which the interface is connected.

- **output_path=**

    Path where /raw /pdf /pcl /txt-jobs /txt-stream directories are created.
    Default: current directory.

- **end_page_timeout=2**

    Time elapsed without receiving data corresponding to the interpretation of
    an end of page. In seconds and > 0.

- **emulation=epson**

    Emulation used. Possible values: epson/escp2 or hp/pcl (or auto Not implemented)


[parallel_printer]
==================

- **delayprinter=0**

    Slow down receiving from computer in micro seconds.


[serial_printer]
================

- **enabled=no**

    Enable/disable the serial printer interface.
    Possible values:

        - no: Only parallel printer will be working;
        - yes: Only serial printer will be working.
        - auto: Let the interface choose the serial printer if it is active
          during its boot process (Not implemented).

- **dtr_logic=high**

    DTR config:

        - high: printer is ready when DSR is asserted (space high level) (default)
        - low: printer is ready when DSR is deasserted (mark low level) (CP2102)

- **baudrate=19200**

    Serial speed. Set it to the computer value. (Usually not above 19200.)

- **flow_control=hardware**

    Serial flow control
    Possible values:

        - hardware: Flow is controlled with DTR (printer)/DSR(computer) pins (default)
        - software: Flow is controlled with XON/XOFF bytes
        - both: Flow is controlled by both methods: hardware + software

