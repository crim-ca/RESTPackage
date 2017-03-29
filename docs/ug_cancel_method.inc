.. _cancel_method:

cancel
++++++

To cancel a given processing request

This method uses HTTP GET.


Parameters:

:uuid: The identifier of a previous processing request.


Return value:

Returns the status of the request after having submitted the cancel
request. Once cancelled, any subsequent status requests will return state as
:ref:`state_revoked`.


Examples:

URL form:

.. code-block:: bash

   <Base URI>/cancel?uuid=6547137e-cc2f-4008-b1eb-4ae8e898ce83
