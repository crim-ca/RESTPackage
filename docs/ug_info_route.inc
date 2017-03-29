.. _information_route:

Information route
+++++++++++++++++

You can obtain information on the current configuration of a deployed instance
by issuing a HTTP GET at the /info route. This will give you information on the
configured services with their expected version, list of route names and so on.


Parameters:

None.


Return value:

A JSON object with the list of configured routes and associated services such
as:

.. code-block:: json

   {
     "services": {
       "transcoder": {
         "category": "Data Storage", 
         "celery_queue_name": "transcoder_0.2.7", 
         "celery_task_name": "transcoder", 
         "doc": "http://some_server/doc.html", 
         "home": "http://some_server/doc.html", 
         "institution": "CRIM", 
         "licence": "http://some_server/doc.html", 
         "name": "Transcoder service", 
         "provenance": "http://some_server/doc.html", 
         "releaseTime": "2015-01-01T00:00:00Z", 
         "releasenotes": "http://some_server/doc.html", 
         "researchSubject": "Multimedia file transcoding", 
         "route_keyword": "transcoder", 
         "source": ",204", 
         "support": "http://some_server/doc.html", 
         "supportEmail": "support@company.com", 
         "synopsis": "RESTful service providing multimedia files transcoding.", 
         "tags": "multimedia,file,transcoding", 
         "tryme": "ssm/tryme.html", 
         "version": "0.2.7"
       }
     }, 
     "version": "1.7.0"
   }


Useful elements are:

:version: The version of the REST API.
:services: Every element in the list is an exposed service through a dynamic
   route. Most elements reflect the requirements of the :ref:`CANARIE API
   <canarie_api_methods>`  specification.

   :version: The expected version of a Service connected through Celery/AMQP.
   :route_keyword: The actual route you use to interact with the API for a
      given service. Note that there might be an additionnal '/info' route for
      the route of a given service. e.g. : "/transcoder/info".
   :doc: A valid URL to the service's documentation.


Examples:

URL form:

.. code-block:: bash

   <Base URI>/info

