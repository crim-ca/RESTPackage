# coding: utf-8

"""
Default configuration values for service gateway package.

Copy this file, rename it if you like, then edit to keep only the values you
need to override for the keys found within.

To have the programs in the package override the values with the values
found in this file, you need to set the environment variable named
"VRP_CONFIGURATION" to the path of your own copy before launching the program.
"""

MY_SERVER_NAME = "localhost"

# Database name relative to the current application directory
DATABASES = {
    'Invocations': {
        'filename': "../static/service_invocations.db",
        'schema_filename': "../static/service_invocations_schema.sql"},
    'Requests': {
        'filename': "../static/requests.db",
        'schema_filename': "../static/requests_schema.sql"}}

CELERY_PROJ_NAME = "worker"
CELERY = {
    'BROKER_URL': "amqp://localhost//",
    'CELERY_RESULT_BACKEND': "amqp://",
    'CELERY_TASK_SERIALIZER': "json",
    'CELERY_RESULT_SERIALIZER': "json",
    'CELERY_ACCEPT_CONTENT': ["json"],
    'CELERY_TASK_RESULT_EXPIRES': 7200}

REQUEST_REGISTER_FN = "static/requests.shelve"

GET_STORAGE_DOC_REQ_URL = ("http://localhost/multimedia_storage"
                           "/get/{storage_doc_id}")
POST_ANNOTATIONS_REQ_URL = ("http://localhost/annotation_storage/"
                            "document/{ann_doc_id}/annotations?storageType=2")

JWT_SIGNATURE_KEY = "vJmMvm44x6RJcVXNPy6UDcSfJHOHNHrT1tKpo4IQ4MU="
JWT_AUDIENCE = "myAudience"
JWT_ALGORITHM = "HS512"
JWT_DURATION = 600  # The following is specified in seconds.


# -- Specific to VestaLoadBalancer --------------------------------------------
# In the following definition, every key is a service.
# Expected values follow this example :
# 'my_service': {
#     # Keyword used in the rest api to access this service
#     # (ex.: http://server/<route_keyword>/info)
#     # Set to '.' to access this service without keyword
#     # (ex.: http://server/info)
#     'route_keyword': 'my_service',
#
#     # The celery task name.
#     # Must match the task in the worker app name : <proj_name>.<task_name>
#     # (ex.: worker.my_service)
#     'celery_task_name': 'my_service',
#
#     # The celery queue name.
#     # Must match the queue name specified when starting the worker
#     # (by the -Q switch)
#     'celery_queue_name': 'my_service_0.1.0',
#
#     # Following parameters are required by the CANARIE API (info request)
#     'name': 'My service',
#     'synopsis': "RESTful service providing my_service.",
#     'version': "0.1.0",  # Expected version - will check.
#     'institution': 'My Organisation',
#     'releaseTime': '2015-01-01T00:00:00Z',
#     'supportEmail': 'support@my-organisation.ca',
#     'category': "Data Manipulation",
#     'researchSubject': "My research subject",
#     'tags': "my_service, research",
#
#     # The following parameters are used to respond to some CANARIE API
#     # request.
#     #
#     # They must be one of the following:
#     #  - A valid URL to perform a redirection
#     #  - A relative template file that will be used to generate the html page
#     #    (relative to the templates directory)
#     #  - A response string and the html status separated by a comma that will
#     #    be used  to make a response to the requested element. Ex.: 'Not
#     #    available,404'
#
#     'home': "http://localhost/docs/my_service.html",
#
#     'doc': "http://localhost/docs/my_service.html",
#     'releasenotes': "http://localhost/docs/my_service.html",
#     'support': "http://localhost/docs/my_service.html",
#
#     # If the source are not provided, CANARIE requires a 204 (No content)
#     # response
#     'source': ",204",
#     'tryme': "http://localhost/docs/my_service.html",
#     'licence': "http://localhost/docs/my_service.html",
#     'provenance': "http://localhost/docs/my_service.html",
#     'os_args': {'image': 'my_service_image_name_v_0.1.0',
#                 'instance_type': 'm1.large'},
#     # Process-request to spawn VM ratio
#     'rubber_params': {'spawn_ratio': 0.1}
#    }

WORKER_SERVICES = {}

BROKER_ADMIN_PORT = '15672'
BROKER_ADMIN_UNAME = 'guest'
BROKER_ADMIN_PASS = 'guest'

# OpenStack acces configuration.
OPS_CONFIG = {'name': 'My OpenStack',
              'cloud_type': 'OpenStack',  # Important so we use the right API.
              'networks': ['ops_net_name'],
              'security_group': ["default"],
              'username': 'MY_USER_NAME',
              'password': 'MY_PASSWORD',
              'tenant_name': 'TENANT_NAME',
              'auth_url': 'http://my.cloud.ca:5000/v2.0',
              'key_name': 'MY_KEY_NAME'}

RUBBER_BACKORDER_THRESHOLD = 3
RUBBER_MAX_VM_QTY = 50  # Maximum number of Virtual machines we can spawn.
# Default seconds to wait between elasticity evaluations:
RUBBER_EVAL_INTERVAL = 120
RUBBER_MIN_IDLE_WORKERS = 1
# Time after which a non-functionnal VM will be terminated:
RUBBER_SLACKER_TIME_THRESHOLD = 300

FLOWER_API_URL = "http://localhost:5555/api"
