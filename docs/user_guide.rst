.. _common_rest_interface:

Common REST interface documentation
===================================


Purpose
-------

This document describes the web service interfaces that are common for each VESTA service. It shows how a service can be used, the standard response types and how to handle exceptions.

.. overview ---------------------------------------------------------------
.. include:: ug_overview.inc

Methods
-------

There are 3 sets of methods available to access services. The first two are specific to their respective front ends which are the Load Balancer and the Multimedia File Storage and the third one is the set of methods required by CANARIE and thus is available on both front ends.


.. Cancel method -------------------------------------------------
.. include:: ug_cancel_method.inc


.. Info route ----------------------------------------------------
.. include:: ug_info_route.inc


.. Status method -------------------------------------------------
.. include:: ug_status_method.inc


.. CANARIE API ---------------------------------------------------
.. include:: ug_canarie_api.inc


.. Error codes section ===========================================
.. include:: ug_error_codes_preamble.inc


.. Core error codes ----------------------------------------------
.. include:: ug_core_error_codes.inc


.. VRP error codes -----------------------------------------------
.. include:: ug_vrp_error_codes.inc


.. Service error codes -------------------------------------------
.. include:: ug_worker_services_error_codes.inc


.. Vision error codes --------------------------------------------
.. include:: ug_vision_error_codes.inc


.. Speech error codes --------------------------------------------
.. include:: ug_speech_error_codes.inc
