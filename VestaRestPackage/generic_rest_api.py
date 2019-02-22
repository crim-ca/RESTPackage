#!/usr/bin/env python
# coding:utf-8

# N.B. : Some of these docstrings are written in reSTructured format so that
# Sphinx can use them directly with fancy formatting.

# In the context of a REST application, this module must be loaded first as it
# is the one that instantiates the Flask Application on which other modules
# will depend.

"""
This module defines the generic REST API for annotation services as defined by
the CANARIE API specification. See :
https://collaboration.canarie.ca/elgg/file/download/849
"""


# -- Standard lib ------------------------------------------------------------
import collections
import datetime
import logging

# -- 3rd party ---------------------------------------------------------------
from flask import render_template
from flask import jsonify

# -- Setup and configuration -------------------------------------------------
from .app_objects import APP, CELERY_APP

# -- Project specific --------------------------------------------------------
from .utility_rest import set_html_as_default_response
from .utility_rest import get_canarie_api_response
from .utility_rest import validate_service_route
from .utility_rest import make_error_response
from .utility_rest import request_wants_json
from .utility_rest import mongo
from .reverse_proxied import ReverseProxied
from .utility_rest import AnyIntConverter
from . import __meta__

# Handle Reverse Proxy setups
APP.wsgi_app = ReverseProxied(APP.wsgi_app)

START_UTC_TIME = datetime.datetime.utcnow()
FL_API_URL = APP.config['FLOWER_API_URL']

# REST requests required by CANARIE
CANARIE_API_VALID_REQUESTS = ['doc',
                              'releasenotes',
                              'support',
                              'source',
                              'tryme',
                              'licence',
                              'provenance']

# HTML errors for which the service provides a custom error page
HANDLED_HTML_ERRORS = [400, 404, 405, 500, 503]
HANDLED_HTML_ERRORS_STR = ", ".join(map(str, HANDLED_HTML_ERRORS))

# Map an error handler for each handled HTML error
# Errors handled here are the ones that occur internally in the application
#
# The loop replace the following code for each handled html error
# @APP.errorhandler(400)
# def page_not_found_400(some_error):
#     return handle_error(400, str(some_error))
#
# For the lambda syntax see the following page explaining the requirement for
# status_code_copy=status_code
# http://stackoverflow.com/questions/938429/scope-of-python-lambda-functions-
# and-their-parameters/938493#938493
for status_code in HANDLED_HTML_ERRORS:
    APP.register_error_handler(status_code,
        lambda more_info, status_code_copy = status_code: \
        make_error_response(html_status=status_code_copy,
                            html_status_response=str(more_info)))


@APP.errorhandler(Exception)
def handle_exceptions(exception_instance):
    """
    Generate error response for raised exceptions.

    :param exception_instance: Exception instance.
    """
    logger = logging.getLogger(__name__)
    logger.debug("Generating error response for the exception %s",
                 repr(exception_instance))
    logger.exception(exception_instance)
    if APP.debug:
        logger.info("In debug mode, re-raising exception")
        raise

    status_code = None
    try:
        status_code = exception_instance.status_code
    except AttributeError:
        logger.info("Processing exception which has no attribute "
                    "«status_code»")
    logger.debug("Status code is %s", status_code)
    response = make_error_response(
        html_status=status_code,
        html_status_response=exception_instance.message,
        vesta_exception=exception_instance)
    return response

# -- Flask routes ------------------------------------------------------------
APP.url_map.converters['any_int'] = AnyIntConverter


@APP.route("/<any_int(" + HANDLED_HTML_ERRORS_STR + "):status_code_str>")
def extern_html_error_handler(status_code_str):
    """
    Handle errors that occur externally provided that Apache is configured so
    that it uses this route for handling errors.

    For this add this line for each handled html errors in the Apache
    configuration::

       ErrorDocument 400 <Rest root>/400
    """
    return make_error_response(html_status=int(status_code_str))


def global_info():
    """
    Return an overview of the services hosted by this REST instance
    """
    info_ = {'version': __meta__.API_VERSION,
             'services': APP.config['WORKER_SERVICES']}
    return jsonify(info_)


@APP.route("/info")
@APP.route("/service/info")
@APP.route("/<service_route>/info")
@APP.route("/<service_route>/service/info")
def info(service_route='.'):
    """
    Required by CANARIE
    A service can define it's service_route as '.', in which case, the URL
    doesn't have to contain a route token
    """
    logger = logging.getLogger(__name__)
    # JSON is used by default but the Canarie API requires html as default
    set_html_as_default_response()

    # Handle the special case where info is requested without any route
    # In this case we return the global info
    if service_route == '.' and \
       service_route not in APP.config['WORKER_SERVICES']:
        return global_info()

    service_name = validate_service_route(service_route)

    service_info_categories = ['name',
                               'synopsis',
                               'institution',
                               'releaseTime',
                               'supportEmail',
                               'category',
                               'researchSubject']
    worker_config = APP.config['WORKER_SERVICES'][service_name]
    service_info = []
    service_info.append(('version', '{0}_{1}'.
                         format(__meta__.API_VERSION,
                                worker_config['version'])))
    for category in service_info_categories:
        cat = worker_config[category]
        service_info.append((category, cat))

    tags = worker_config['tags']
    service_info.append(('tags', tags.split(',')))

    # Get information on registered workers ---------------------
    queue_name = worker_config['celery_queue_name']
    logger.info("Refreshing knowledge on all worker queues")
    inspector = CELERY_APP.control.inspect()
    active_queues = inspector.active_queues()

    logger.debug("Worker info : %s", active_queues)
    logger.debug("Queue info : %s", queue_name)

    active_workers = 0

    if active_queues:
        for _ql_ in active_queues.values():
            for _q_ in _ql_:
                if queue_name in _q_['name']:
                    active_workers += 1

    logger.info("There are %s known workers found", active_workers)
    service_info.append(('activeWorkers', active_workers))

    service_info = collections.OrderedDict(service_info)

    if request_wants_json():
        return jsonify(service_info)
    return render_template('default.html', Title="Info", Tags=service_info)


@APP.route("/stats")
@APP.route("/<service_route>/stats")
@APP.route("/<service_route>/service/stats")
def stats(service_route='.'):
    """
    Required by CANARIE.
    A service can define it's service_route as '.', in which case, the URL
    doesn't have to contain a route token
    """
    logger = logging.getLogger(__name__)
    logger.info("Requested stats for service %s", service_route)
    # JSON is used by default but the Canarie API requires html as default
    set_html_as_default_response()

    service_name = validate_service_route(service_route)

    service_stats = {}
    service_stats['lastReset'] = START_UTC_TIME.strftime('%Y-%m-%dT%H:%M:%SZ')
    service_stats['invocations'] = mongo.db.Invocations.count({"datetime": {"$gt": START_UTC_TIME}})

    if request_wants_json():
        return jsonify(service_stats)

    return render_template('default.html', Title="Stats", Tags=service_stats)


@APP.route("/")
@APP.route("/<any(" +
           ",".join(CANARIE_API_VALID_REQUESTS) + "):api_request>")
@APP.route("/<service_route>/<any(" +
           ",".join(CANARIE_API_VALID_REQUESTS) + "):api_request>")
@APP.route("/<service_route>/service/<any(" +
           ",".join(CANARIE_API_VALID_REQUESTS) + "):api_request>")
def simple_requests_handler(api_request='home', service_route='.'):
    """
    Handle simple requests required by CANARIE
    A service can define it's service_route as '.', in which case, the URL
    doesn't have to contain a route token
    """

    # JSON is used by default but the Canarie API requires html as default
    set_html_as_default_response()

    return get_canarie_api_response(service_route, api_request)


def configure_home_route():
    """
    Configure the route /<service_route>

    Cannot be done with the decorator because we must know the exact routes
    name and not match any keyword since it will conflict with other route like
    /info, /doc, etc.
    """
    logger = logging.getLogger(__name__)
    logger.debug("Current configuration is : %s", APP.config)
    logger.debug("Root path is %s", APP.root_path)
    logger.info("Static path is %s", APP.static_folder)

    known_services_routes = list(APP.config['WORKER_SERVICES'].keys())
    logger.info("Configuring home route for services %s",
                known_services_routes)

    routes = [r for r in known_services_routes if r != '.']

    if len(routes) > 0:
        rule = '/<any({0}):service_route>/'.format(','.join(routes))
        logger.debug("Adding route rule : {0}".format(rule))
        APP.add_url_rule(rule, None, simple_requests_handler)

    logger.debug("Flask url map: {0}".format(APP.url_map))