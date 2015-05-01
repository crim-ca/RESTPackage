from os import environ

from flask import Flask

from . import default_configuration
from . import celery_init

APP = Flask(__name__)

APP.config.from_object(default_configuration)

# If user supplied an environment variable for custom config, use it.
if 'VRP_CONFIGURATION' in environ:
    APP.config.from_envvar("VRP_CONFIGURATION")

# N.B.: Logs for this function won't work except if initialized before import.
CELERY_APP = celery_init.configure(APP.config)
