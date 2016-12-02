.. _common_rest_interface:

Common REST interface documentation
===================================


Purpose
-------

This document describes the web service interfaces that are common for each
VESTA service. It shows how a service can be used, the standard response types
and how to handle exceptions.

.. overview ---------------------------------------------------------------
.. include:: ug_overview.rst

Methods
-------

There are 3 sets of methods available to access services. The first two are
specific to their respective front ends which are the Load Balancer and the
Multimedia File Storage and the third one is the set of methods required by
CANARIE and thus is available on both front ends. 




.. include:: ug_cancel_method.rst


.. Info route ----------------------------------------------------
.. include:: ug_info_route.rst


.. Status method -------------------------------------------------
.. include:: ug_status_method.rst


.. CANARIE API ---------------------------------------------------
.. include:: ug_canarie_api.rst


.. Error codes section ===========================================
.. include:: ug_error_codes_preamble.rst


.. Core error codes ----------------------------------------------
.. include:: ug_core_error_codes.rst


.. VRP error codes -----------------------------------------------
.. include:: ug_vrp_error_codes.rst


.. Service error codes -------------------------------------------
.. include:: ug_worker_services_error_codes.rst


.. MSS error codes -----------------------------------------------
.. include:: ug_mss_error_codes.rst


.. Vision error codes --------------------------------------------
.. include:: ug_vision_error_codes.rst


.. Speech error codes --------------------------------------------
.. include:: ug_speech_error_codes.rst
