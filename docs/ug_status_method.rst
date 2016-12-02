.. _status_method:

Status method
+++++++++++++

For methods requiring asynchronous tasks, there is a also a corresponding
method that lets monitor the status of submitted tasks. The response format of
this method is uniform across all services and contains 3 keys :

* uuid
* status
* result

For example:

.. code-block:: json

   {
       "result": {
           "worker_id_version": "0.1.0",
           "current": 73,
           "start_time": "2014-09-10T12:23:19", 
           "total": 100
       },
       "status": "PROGRESS",
       "uuid": "f1b40709-ca76-4554-b19f-277b2f8d5d49"
   }


UUID
~~~~

The identifier of a task supplied by the user which was used to perform the
initial status query.


Status key values (Service States)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Current status of a task that can be one of the following values:

* PENDING
* RECEIVED
* STARTED
* PROGRESS
* STORING
* FAILURE
* SUCCESS
* REVOKED
* RETRY
* EXPIRED

The states which are listed above are essentially the states reported by the
underlying distributed processing queue system. In this case we use the `Celery
<http://www.celeryproject.org/>`_ solution. Each status has a more in depth
explanation in the result section below, but for a generic documentation about
the reported states, one can also see the following document supplied by
Celery:

http://celery.readthedocs.org/en/latest/reference/celery.states.html?highlight=states#misc

In addition to the Celery states, there are three custom states. The first is a
custom state which is PROGRESS. This state means that the underlying service
has updated a progress value that can be used to determine estimated time of
completion for the given task. The other custom states that could be received
are STORING and EXPIRED. See below for more information on possible states.


.. _states:

Result (variable)
~~~~~~~~~~~~~~~~~

A general variable that might hold different information depending on the
aforementioned status value. For instance, when a processing request has
concluded to an error state, information on the error will be reported in the
result variable. Hence one must check the value of the status variable to know
how to consume the result variable. The following states yield useful
information in the result variable:


.. _state_pending:

pending
```````

The task has been submitted to a queue and is waiting to be processed by a
worker. The time it may take before the processing starts depends on how many
tasks have been previously submitted to the processing queue and how many
workers are available to process this type of task. The worst case would be
that there are no workers at all which are available to consume the given tasks
at this time and thus the task may never be processed. The result for this
status is always null::

   {
       "result" : null
   }


.. _state_received:

received
````````

The task has been received by a worker. At this point we know that the task
will be processed and a progress status should be available soon. There is
still no result::

   {
       "result" : null
   }


.. _state_started:

started
```````

The worker has started working on the task and a progress status should be
available imminently. There is still no result::

   {
       "result" : null
   }


.. _state_progress:

progress
````````

The worker is doing some progress. The result variable will hold information
about the progress of the task completion when in progress state. e.g.:

.. code-block:: json

   {
       "result" : {
          "worker_id_version": "0.1.43",
          "host": "david-transition.novalocal",
          "type": "transition",
          "start_time": "2014-09-10T12:23:19", 
          "current": 12,
          "total": 100
       }
   }

The key «current» documents the last reported progress state. «total» gives us
the upper boundary of the progress scale. Thus in this case we are told that
progress is at 12/100 (12%). The «start_time» can also be used to estimate the
task remaining time : remaining_time = (now - start_time) * (total - current) /
current. There is also some information on the worker like its «type», which
the service name, the «host», which is where the worker is running and the
«worker_id_version», which is the version of the worker.


.. _state_storing:

storing
```````

The worker is storing annotations on the annotation server. This state arises
when the annotation service was called with instructions to save the
annotations on an Annotations Storage Service back-end by issuing an
annotations process request along with the «ann_doc_id» variable. In this
context, the STORING state will be a transient state indicating that the call
to the Annotations Storage Service is in effect and not yet complete. If the
annotation process request was not issued with instructions to save to an
Annotations Storage Service back-end then this state should not surface. The
result structure is the same than the progress one except for the key «current»
and «total» which are omitted:

.. code-block:: json

   {
       "result" : {
           "worker_id_version": "0.1.43",
           "host": "david-transition.novalocal",
           "type": "transition",
           "start_time": "2014-09-10T12:23:19"
       }
   }


.. _state_failure:

failure
```````

The worker failed while processing the task. The result will give more details
about the cause of failure. e.g.:

.. code-block:: json

   {
       "result" : {
           "code": 301,
           "message": "HTTP Error 404: Not Found"
       }
   }

The keys «code» and «message» are the same as those used in the general
exceptions handling and are documented in depth in the "Service exceptions"
section at the bottom of this page.


.. _state_success:

success
```````

The worker successfully completed the task. The result variable will hold the
task output when in success state, which consists in an array of annotations.
Each service will have a common property set for each annotation following by
their specific properties since they have different outputs. This is what
could be obtained:

.. code-block:: json

   {
       "result": [ 
           { 
               "@id": "diarisation_annotation", 
               "@version": "0.5.1", 
               "specific_property": "A",
               "meaning_of_life": "Not sure"
           },
           { 
               "@id": "diarisation_annotation", 
               "@version": "0.5.1", 
               "specific_property": "B",
               "meaning_of_life": 42
           }
       ]
   }

These fields are common to all annotators:

:@id: Indicates the worker type
:@version: Indicates the worker version.


.. _state_revoked:

revoked
```````

The task has been revoked which implies that the user cancelled the task
through the REST interface. The result field is the same as for the Failure
status, so it is possible to get more details on the revocation. The error code
should always be 109, associated with the TaskRevokedError exception raised by
a worker when its task is revoked. The message contains the revocation status.
Among the possible values for the revocation status there is "revoked" which
imply that the task has been revoked before any processing and "terminated"
which means that the task had to be killed because it had already started. A
revoked status with a result "terminated" should not be confused with a success
status with a result structure : "terminated" means that the task has been
killed and has nothing to do with the French word "terminée". Example result:

.. code-block:: json

   {
       "result" : {
           "code": 109,
           "message": "terminated"
       }
   }


.. _state_retry:

retry
`````

The worker failed while processing the task but has requested a new attempt to
complete the task. The task has been re-submitted to a queue and should be
picked up by again by another worker. By default, a delay of 180 seconds will
be observed before starting the process again. The result field is the same as
for the Failure status, so it is possible to know the cause of the failure
which triggered a new processing attempt. 


.. _state_expired:

expired
```````

This state is returned in the case where the queue has been idle for more than
2 hours and has been removed. The uuid is no longer useful once this state is
declared since the task does not exist anymore. The result associated with this
state is null::

   {
       "result" : null
   }


.. _canarie_api:

