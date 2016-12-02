.. _vrp_error_codes:

REST services package error codes
+++++++++++++++++++++++++++++++++

====    ===========
Code    Description
====    ===========
200     System settings loading exception.
201     One or many workers have a different REST API configured in their
        configuration files.
202     An unknown service is being used. Use the /info request to get
        available services on the current server.
203     An unknown task UUID is being used for a /status or a /cancel request.
204     The declared worker version in the server configuration file doesn't
        match the one produced by the worker itself.
205     There is a problem in the communication with the AMQP server.
206     The request has been made without a required parameter.
207     A task request has been made without a valid document URL.
====    ===========
