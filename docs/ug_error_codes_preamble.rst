.. _error_codes:

Service Exceptions and error codes
----------------------------------

When something goes wrong the system will return error responses which are
documented here. Because service exceptions are handled in a uniform manner
independently of the service that is being used, users can expect the same
response format across the system. Because services target a computer use and
not humans, the server will return exceptions in JSON format by default, unless
that the 'text/html' format is explicitly requested via the 'Accept' header.
In addition, to comply with :ref:`CANARIE API <canarie_api_methods>` and
because these requests should be used by humans, they will, by default, return
error in html format unless that the header mentions the 'application/json'
format. 

The JSON response takes over the response status and reason for clarity purpose
and appends an error code and message under the Vesta key specific to the
underlying system. e.g.:

.. code-block:: json

   {
       "status": 400,
       "description": "Bad request",
       "vesta": {
           "code": 206,
           "message": "A GET on the URI '/status' requires the following parameter : uuid"
       }
   }

The keys «status» and «description» can take any values defined by the HTTP
standard but the first table give an overview of the most frequent status that
could be received. The key «Vesta» contains a structure composed of the keys
«code» and «message» that give a specific information on the exception cause. 

The next tables shows the various HTTP status codes that could be received and
the following one lists all the internal error code and their explanations.  

======  ===========
Status  Description
======  ===========
200     Successful request, results follow
204     Request was properly formatted, no content
400     Bad request due to improper specifications, unrecognized parameter,
        parameter value out of range, etc.
404     The requested resource was not found
500     Internal server error
503     Service temporarily unavailable
======  ===========
