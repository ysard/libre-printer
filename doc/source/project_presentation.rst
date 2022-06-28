.. _project_presentation:

********************
Project presentation
********************

.. contents:: Summary
    :depth: 2
    :local:
    :backlinks: top

Features
========

.. mermaid::
   :align: center

    graph TD
        A[fa:fa-computer-classic Host] -->|Serial RS-232 data| B[fa:fa-microchip Libre-Printer interface]
        A --> |Parallel Centronics data| B
        B -->|fa:fa-usb USB| C[fa:fa-laptop RaspberryPi or Computer]
        C --> Raw[fa:fa-file Raw file]
        Raw --> D[fa:fa-file-pdf PDF]
        Raw --> E[fa:fa-align-justify Text]
        Raw --> F[fa:fa-file-image PNG]
        Raw -->|fa:fa-usb USB| G[fa:fa-print Modern printer]
        Raw -->|fa:fa-network-wired Network| G


Libre-Printer consists of an Arduino interface and a set of programs designed to pretend
to be a Centronics parallel or serial printer. The data received is stored and/or redirected
to a modern printer connected via USB or the network.

The interface connects via USB to any computer or microcomputer such as a Raspberry Pi
(all models, including the Zero models).

The operation can be summarized in 3 key steps:

- Capture data from the sending machine;
- Rendering the data in plain text, PDF or image format;
- Redirection of the stream to a modern printer (e.g. network printer)


Printer types & protocols supported
===================================

The interfaces concerned are the following:

- Epson printers: ESC/P - ESC/P2, 9 & 24 pins
- HP PCL printers:
    Any resolution and format (Ex: 150dpi, 300dpi, 600dpi), color or grayscale
    thanks to the project
    `GhostPCL <https://www.ghostscript.com/doc/9.53.3/WhatIsGS.htm#GhostPCL>`_.

Connectivity
============

Connections can be both serial RS-232 and parallel Centronics (DB-25 on one end,
36-pins Centronics on the other).

See the chapter :ref:`interface_type` for more information.

.. _project_structure:

Structure
=========

Hardware Interface
------------------

Instead of opting for an expensive, low scalability and reverse engineering
hindering interface board like the original project, it is cheap chips from the
Arduino ecosystem.

Currently (and in a non-limited way) it is an Arduino ProMicro from Sparkfun,
copies of which are available on many resale sites.

This chip has enough pins to accommodate a parallel interface without an intermediate
component, as well as 2 RS-232 serial interfaces. One of the two serial interfaces
is emulated on USB and allows the connection, the exchanges and the update of the
Arduino from a simple USB plug (we avoid the proprietary connectors or the limited
use of a RaspberryPi HAT).

Software
--------

The core software collecting the data interpreted by the interface can be executed
on any machine running GNU/Linux.

It should be noted that the recent versions of the program converting ESC/P and
ESC/P2 data are those of the Retroprinter project, which has only been compiled
for the ARM platform (i.e. Raspberry Pi).
However, we offer a slightly older (but functional) version of the converter that
is compilable on all platforms.


Why this project?
=================

Why a competing project to RetroPrinter?

- Because we can.
- In short: This is an opportunity to have a better community project than the
  proprietary version.

Technical considerations
------------------------

- The original software is not maintainable (close source), without decent software
  design and unnecessarily cumbersome.
- The ESC/P2 converter of RetroPrinter has a "free version" which besides being
  lightened of some features (missing international charsets, etc.) is offered
  to be tested for free by the community and then to bring patches in the paid
  version of their product...
- The "free version" is buggy and sometimes not compilable due to "patches"
  (obviously applied with little testing).
- The documentation of the original programs is overloaded, poorly updated,
  with redundant/overlapping parameters and sometimes non-functional combinations.
- The RetroPrinter interface is limited to a handful of platforms and cannot be
  a usable product for most people without some investment (let's not forget that
  in **the last few years the prices of RaspberryPi type boards have skyrocketed**!).
  Making the project compatible with all platforms is both an economical and
  pragmatic choice for its diffusion


- |project_name| components are much cheaper/more affordable.
- We support serial printers without additional adapters.
- Multiple interfaces can be connected on the same computer!
- Our code is tested with over 90% coverage.


Ethical considerations
----------------------

Our solution is **truly** free: licensed under the AGPL.

It is common to see programs in C/C++ etc. developed not by expertise or by
performance research, but rather by a desire to obfuscate code at "lower cost".
RetroPrinter is no exception to this.
Thus the "community" formed around these projects receives few benefits:
slow development of patches, lack of know-how for some tasks, paying products,
no right to modify or redistribute the program, etc.
This behaviour is toxic because the community can neither audit nor improve the
products. The most paradoxical thing is that when the proprietary code leaks
(and it always does) it becomes a competitor to the original
(Cf. `Streisand effect <https://fr.wikipedia.org/wiki/Effet_Streisand>`_;
which is precisely what the authors wanted to avoid in the first place.

Finally, quite frankly, let's be pragmatic, the technologies of the 80's don't
need the proprietary and paying overlay of the 2022's... Let's hear it.

