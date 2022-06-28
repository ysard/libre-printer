.. _interface_usage:

***************
Interface usage
***************

As it was mentioned in the project presentation chapter (:ref:`project_structure`),
|project_name| relies on an interface that receives the print data coming from
a computer.

The interface is currently an Arduino ProMicro whose diagram below:

.. figure:: _static/pinouts/pro_micro_pinout_1.png
   :scale: 75 %
   :align: center
   :alt: Arduino ProMicro pinout

   Arduino ProMicro pinout

.. contents:: Summary
    :depth: 2
    :local:
    :backlinks: top

LED indications
===============

================================================ ===========================================
**Power LED (green)**                            Lit as soon as the interface is powered on
**TX LED only (red)**                            Interface waiting for configuration
**RX LED flashes at a rate of 1/second (red)**   Interface ready to receive print data
**RX LED flashes briefly + TX LED continuously** Interface receiving data and relaying it
**TX LED + RX LED during ~7seconds**             Interface in boot mode after a manual reset
================================================ ===========================================

Datasheet
=========

TBR
