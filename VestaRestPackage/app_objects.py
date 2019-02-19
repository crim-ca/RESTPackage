"""
This module serves the purpose of centralizing the state objects of Flask and
Celery in a single place.
"""


from os import environ

# -- 3rd party modules -------------------------------------------------------
from flask import Flask

from . import default_configuration
from . import celery_init
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

sentry_sdk.init(
    integrations=[FlaskIntegration()]
)


APP = Flask(__name__)

APP.config.from_object(default_configuration)

# If user supplied an environment variable for custom config, use it.
if 'VRP_CONFIGURATION' in environ:
    print("Using configuration file {0}".format(environ['VRP_CONFIGURATION']))
    APP.config.from_envvar("VRP_CONFIGURATION")
else:
    print("No user-supplied configuration file. Using package defaults.")

# N.B.: Logs for this function won't work except if initialized before import.
CELERY_APP = celery_init.configure(APP.config)
