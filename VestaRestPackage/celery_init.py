#!/usr/bin/env python
# coding:utf-8


"""
This module configures the Celery app using proper config params.
"""


# -- Standard lib ------------------------------------------------------------
import logging

# --3rd party modules---------------------------------------------------------
from celery import Celery


def configure(config):
    """
    Configures the celery application.

    A given service name will have its requests route through a queue named
    like the REST route.

    :param config: Dict like object with Celery configuration values.
    :returns: Reference to the Celery application to keep handy.
    """
    logger = logging.getLogger(__name__)

    proj_name = config['CELERY_PROJ_NAME']
    logger.debug("Celery project name is %s", proj_name)
    celery_app = Celery(proj_name)
    celery_app.config_from_object(config['CELERY'])
    return celery_app
