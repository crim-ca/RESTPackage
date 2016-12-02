#!/usr/bin/env python
# coding:utf-8


"""
This module configures the celery app using proper config params.
"""


# -- Standard lib ------------------------------------------------------------
import logging

# --3rd party modules---------------------------------------------------------
from celery import Celery


def configure(config):
    """
    Configures the celery routes based on the REST routes.
    A given service name will have its requests route through a queue named
    like the REST route.

    :returns: Reference to the Celery application to keep handy.
    """
    logger = logging.getLogger(__name__)

    proj_name = config['CELERY_PROJ_NAME']
    celery_app = Celery(proj_name)
    celery_app.config_from_object(config['CELERY'])
    # celery_app.conf.update(config['CELERY'])

    celery_routes = dict()

    workers = config['WORKER_SERVICES']

    logger.info(u"Configuring Celery task names from routes for services: {s}"
                .format(s=workers.keys()))
    for w_config in workers.values():
        service_name = w_config['celery_task_name']
        celery_task = '{n}.{t}'.format(n=proj_name, t=service_name)
        queue_name = {'queue': w_config["celery_queue_name"]}
        celery_routes[celery_task] = queue_name

    logger.info(u"Configured Celery routes are: {0}".format(celery_routes))

    celery_app.conf.update(CELERY_ROUTES=celery_routes)
    return celery_app