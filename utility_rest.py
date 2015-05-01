#!/usr/bin/env python
# coding:utf-8

"""
This module is a collection of utility functions used by the rest_route module
placed here to keep the rest_route module as clear as possible.
"""


# -- Standard lib ------------------------------------------------------------
from urlparse import urlparse
import ConfigParser
from os import path
import traceback
import threading
import httplib
import sqlite3
import logging
import sys
import re

# -- 3rd party ---------------------------------------------------------------
from werkzeug.datastructures import MIMEAccept
from werkzeug.routing import BaseConverter
from flask import render_template
from flask import make_response
from flask import current_app
from flask import redirect
from flask import request
from flask import jsonify
from flask import Markup
from flask import g

# -- Project specific --------------------------------------------------------
from .Service.request_process_mesg import (WorkerExceptionWrapper,
                                           send_task_request,
                                           get_request_info,
                                           cancel_request)
from .vesta_exceptions import (DocumentUrlNotValidException,
                               MissingParameterError,
                               VersionMismatchError,
                               UnknownServiceError,
                               UnknownUUIDError,
                               VestaExceptions,
                               AMQPError)
from .app_objects import APP, CELERY_APP


def request_wants_json():
    """
    Check if the request type is JSON

    The default mimetype */* is interpreted as JSON.
    """

    # Best will be JSON if it's in accepted mimetypes and
    # has a quality greater or equal to HTML.
    # For */* both JSON and HTML will have the same quality so JSON still win
    choices = ['application/json', 'text/html']
    best = request.accept_mimetypes.best_match(choices)
    return best == 'application/json'


def set_html_as_default_response():
    """
    By default if the accept mimetypes contains */*, JSON format will be used.
    By calling this function, the */* mimetype will be changed explicitely into
    text/html so that it becomes the mimetype used by default.
    """

    # Best will be HTML if it's in accept mimetypes and
    # has a quality greater or equal to json.
    # For */* both json and HTML will have the same quality so HTML still wins
    best = request.accept_mimetypes.best_match(['text/html',
                                                'application/json'])
    # Replace any */* by HTML so that json isn't picked by default
    if best == 'text/html':
        request.accept_mimetypes = \
            MIMEAccept([('text/html',
                         request.accept_mimetypes['text/html'])])


def validate_service_route(service_route):
    """
    Check if service name is a value amongst known services in the
    configuration.

    :param service_route: Route name of the service coming from the URL e.g.:
                          ['diarisation', 'stt', etc.]
    :returns: Service name associated with the route
    :raises: UnknownServiceError
    """
    if service_route not in APP.config['WORKER_SERVICES']:
        raise UnknownServiceError(service_route)
    route = APP.config['WORKER_SERVICES'][service_route]['route_keyword']
    return route


def validate_uuid(uuid, service_name):
    """
    Validate UUID existence for a given service.

    :param uuid: UUID of a given request
    :type uuid: Unicode
    :param service_name: Name of the service which is requested.
    :type service_name: string
    :raises: UnknownUUIDError in case that the UUID
             isn't owned by the given service.
    """
    logger = logging.getLogger(__name__)
    query = 'select count(*) from requests where service = ? and uuid = ?'

    logger.debug(u"Accessing information for request «{0}» to {1}"
                 .format(uuid, service_name))

    database = get_requests_db()
    cur = database.execute(query, [service_name, uuid])
    rows = cur.fetchall()
    cur.close()
    if rows[0][0] == 0:
        raise UnknownUUIDError(uuid)


def validate_state(uuid, service_name, state):
    """
    Validate the state of a given task.

    - Check that the activity flag is True
        if the task has leave the PENDING status
    - Check that the worker version in the payload fit the config one

    :param uuid: UUID of a given request
    :type uuid: Unicode
    :param service_name: Name of the service which is requested.
    :type service_name: string
    :param state: The state of the task
    :type state: dict containing task status
    :raises: VersionMismatchError in case of a version mismatch
    """
    logger = logging.getLogger(__name__)
    select_query = ('select activity from requests where '
                    'service = ? and uuid = ?')
    logger.debug(u"Verifying the activity flag in db "
                 u"for request «{0}» to {1}"
                 .format(uuid, service_name))

    database = get_requests_db()
    cur = database.execute(select_query, [service_name, uuid])
    rows = cur.fetchall()
    activity_flag = rows[0][0]
    cur.close()

    if state['status'] == 'PENDING':
        # The task is pending: Check the activity flag, in case it is on,
        #                      the task has expired and is no more PENDING
        if activity_flag:
            state['status'] = 'EXPIRED'

            logger.debug(u'Status of task {0} for {1} is reported as PENDING, '
                         u'but the task has been running. The task queue has '
                         u'EXPIRED'.format(uuid, service_name))

    elif not activity_flag:
        # The task is being executed: Ensure that the activity flag is on.

        update_query = ('update requests set activity=? where '
                        'service = ? and uuid = ?')

        logger.debug(u"Turning on the activity flag in db "
                     u"of task «{0}» for {1}"
                     .format(uuid, service_name))

        cur = database.execute(update_query, [True, service_name, uuid])
        cur.close()
        database.commit()

    if state['status'] == 'PROGRESS':
        payload_ver = state['result']['worker_id_version']
        decl_ver = APP.config['WORKER_SERVICES']['version']

        if payload_ver != decl_ver:
            msg = (u'Service {serv} declares the version {decl_ver} '
                   u'in its config file but messages received from its worker '
                   u'contain the version {payload_ver}.'
                   .format(serv=service_name,
                           decl_ver=decl_ver,
                           payload_ver=payload_ver))
            raise VersionMismatchError(msg)

    return state


def store_uuid(uuid, service_name):
    """
    Store a UUID so it can be validated later.

    :param uuid: UUID of a given request
    :type uuid: Unicode
    :param service_name: Name of the service which is requested.
    :type service_name: string
    """
    logger = logging.getLogger(__name__)
    query = 'insert into requests values(CURRENT_TIMESTAMP, ?, ?, ?)'

    logger.debug(u"Keeping track of request «{0}» for {1}".
                 format(uuid, service_name))

    database = get_requests_db()
    cur = database.execute(query, [service_name, uuid, False])
    cur.close()
    database.commit()


def async_fct_wrapper(out_dict, fct, *args, **kwargs):
    logger = logging.getLogger(__name__)
    try:
        logger.debug("args : {0}".format(args))
        logger.debug("kwargs : {0}".format(kwargs))
        out_dict['return_value'] = fct(*args, **kwargs)
        logger.debug("out_dict : {o}".format(o=out_dict))
    except:
        out_dict['exception'] = sys.exc_info()


def async_call(fct, *args, **kwargs):
    """
    Call AMQP functions with any arg or kwargs in an asynchronous manner

    :param fct: The function to call asynchronously
    :param args: Arguments
    :param kwargs: Keyword arguments
    :return: The function output
    :raises: AMQPError if a timeout occurs
    """
    out_dict = {'return_value': None, 'exception': None}
    args_augmented = (out_dict, fct)
    args_augmented += args
    thr = threading.Thread(target=async_fct_wrapper,
                           args=args_augmented,
                           kwargs=kwargs)
    thr.start()
    thr.join(timeout=5)
    if thr.is_alive():
        raise AMQPError()

    if out_dict['exception'] is not None:
        exc = out_dict['exception']
        raise exc[0], exc[1], exc[2]

    return out_dict['return_value']


def get_request_url(request_type, kwargs):
    logger = logging.getLogger(__name__)
    logger.debug("Args are : {0}".format(kwargs))
    request_url = APP.config[request_type]
    return request_url.format(**kwargs)


def validate_url(url):
    """
    Check if URL is invalid.
    """
    logger = logging.getLogger(__name__)
    logger.debug(u"Validating URL : {0}".format(url))
    url_p = urlparse(url)
    if not url_p.scheme or not url_p.netloc or not url_p.path:
        raise DocumentUrlNotValidException(url)


def submit_task(storage_doc_id, task_name, service_route='.', **extra_params):
    """
    Submit a task to a worker.

    :param storage_doc_id: The document ID for which a task should be run.
    :param task_name: The task name for logging purposes
    :param service_route: service route to obtain the requested service name
    :param extra_params: Extra parameters that are passed to send_task_request
    :returns: JSON object with the task UUID or error response.
    """
    logger = logging.getLogger(__name__)
    service_name = validate_service_route(service_route)
    params = extra_params

    if service_route == '.':
        friendly_task_name = task_name
    else:
        friendly_task_name = '{0} by {1}'.format(task_name, service_name)

    if storage_doc_id is None:
        # If storage_doc_id is None a full doc_url must be given
        if 'doc_url' not in request.values:
            raise MissingParameterError('POST',
                                        '/{0}'.format(task_name),
                                        'doc_url')

        # request.values combines values from args and form
        doc_url = request.values['doc_url']

        logger.info(u'Submitting "{task}" task with public url : {url}'
                    .format(task=friendly_task_name, url=doc_url))
    else:
        doc_url = get_request_url('GET_STORAGE_DOC_REQ_URL',
                                  {'storage_doc_id': storage_doc_id})

        logger.info(u'Submitting "{task}" task with storage doc id : {doc_id}'
                    .format(task=friendly_task_name, doc_id=storage_doc_id))

    validate_url(doc_url)

    # For all storage_*_id given in request.values, resolve them if necessary
    # and add them to the misc data holder to async_call
    is_storage_arg = lambda x: x.startswith('storage_') and x.endswith('_id')
    is_url_arg = lambda x: x.endswith('_url') and x != 'doc_url'

    storage_args = filter(is_storage_arg, request.values.keys())
    url_args = filter(is_url_arg, request.values.keys())

    if storage_args or url_args:
        if 'misc' not in params:
            params['misc'] = {}

        logger.debug(u"{l} arguments referencing storage ids: {a}".
                     format(l=len(storage_args), a=storage_args))

        for storage_arg in storage_args:
            url_ = None
            # E.g.: If "storage_txt_id" then doctype == 'txt'
            doctype = storage_arg.split('_')[1]
            direct_url_arg = "{0}_url".format(doctype)
            if direct_url_arg in request.values.keys():
                # Here we could also consider raising an exception.
                logger.warning(u"Conflicting arguments {0} and {1}, "
                               u"defaulting to {1}".
                               format(storage_arg, direct_url_arg))
                # Preference given to the direct URL
                url_ = request.values[direct_url_arg]
            else:
                id_ = request.values[storage_arg]
                url_ = get_request_url('GET_STORAGE_DOC_REQ_URL',
                                       {'storage_doc_id': id_})
                logger.debug(u"Resolving URL for id {0} of type {1}: {2}".
                             format(id_, doctype, url_))

            validate_url(url_)
            logger.info(u"Using argument {0}={1}".format(storage_arg, url_))
            params['misc'][direct_url_arg] = url_

        # For all *_url given in request.values, add them to the misc data
        # holder to async_call
        logger.debug(u"{l} arguments referencing direct URLs other than"
                     u" doc_url: {u}".format(l=len(url_args), u=url_args))
        for url_arg in url_args:
            url_ = request.values[url_arg]
            validate_url(url_)
            logger.info(u"Using argument {0}={1}".format(url_arg, url_))
            params['misc'][url_arg] = url_

    log_request(service_name, 'POST {request} request on {doc_url}'
                .format(request=task_name, doc_url=doc_url))

    worker_config = APP.config['WORKER_SERVICES'][service_name]
    celery_task_name = worker_config['celery_task_name']
    params['url'] = doc_url
    params['name'] = celery_task_name
    params['app'] = CELERY_APP
    async_result = async_call(send_task_request, **params)

    logger.info(u'"{task}" task submitted for {doc_url} -> UUID = {uuid}'.
                format(task=friendly_task_name,
                       doc_url=doc_url,
                       uuid=async_result.task_id))

    store_uuid(async_result.task_id, service_name)

    return jsonify({'uuid': async_result.task_id})


def uuid_task(task, service_route='.'):
    """
    Get the status or cancel a task identified by a UUID.

    :param task: status or cancel
    :param service_route: service route to obtain the requested service name
    :returns: JSON object with latest status or error response.
    """
    logger = logging.getLogger(__name__)
    service_name = validate_service_route(service_route)
    if 'uuid' not in request.args:
        raise MissingParameterError('GET', '/{0}'.format(task), 'uuid')

    request_uuid = request.args.get('uuid', '')
    log_request(service_name, '{op} on {uuid}'.format(op=task,
                                                      uuid=request_uuid))

    logger.info(u'{task} request on task {uuid} for {serv}'.
                format(task=task, uuid=request_uuid, serv=service_name))
    validate_uuid(request_uuid, service_name)

    if task == 'cancel':
        async_call(cancel_request, request_uuid, CELERY_APP)
    state = async_call(get_request_info, request_uuid, CELERY_APP)
    state = validate_state(request_uuid, service_name, state)
    return jsonify(state)


def get_canarie_api_response(service_route, canarie_api_request):
    """
    Provide a valid HTML response for the canarie api request based on the
    service_route.

    :param service_route: Route name of the service coming from the URL e.g. :
                          ['diarisation', 'stt', etc.]

    :param canarie_api_request: The request specified in the URL
    :returns: A valid HTML response
    """

    service_name = validate_service_route(service_route)

    # The service config should return either :
    #      - A valid URL (in which case a redirection is performed)
    #      - A relative template file from which an HTML page is rendered
    #      - A comma separated list corresponding to the response tuple
    #      (response, status)
    worker_config = APP.config['WORKER_SERVICES'][service_name]
    cfg_val = worker_config[canarie_api_request]

    template_folder = APP.template_folder
    if cfg_val.find('http') == 0:
        return redirect(cfg_val)
    elif path.isfile(path.join(template_folder, cfg_val.rsplit('#', 1)[0])):
        return render_template(cfg_val)
    elif len(cfg_val.split(',')) == 2:
        return make_response(*(cfg_val.split(',')))
    else:
        msg = ("The service does not provide in it's configuration file a "
               "valid source for some of the CANARIE request API like "
               "documentation, support, etc. .)")
        raise ConfigParser.Error(msg)


def make_error_response(html_status=None,
                        html_status_response=None,
                        vesta_exception=None):
    """
    Make an error response based on the request type and given information.

    :param html_status: HTML status, if not provided it will be extracted
                from the vesta_exception (at least one of html_status or
                vesta_exception must be provided)
    :param html_status_response: Standard message associated with a status
                code. Obtained via httplib if not provided.
    :param vesta_exception: Vesta exception instance used to obtain an
                exception code. Generic one is used if not provided.
    """
    logger = logging.getLogger(__name__)
    vesta_exc_instance = VestaExceptions.Instance()

    # Extract the real exception from a WorkerExceptionWrapper if required
    is_worker_exc = False
    real_exception = vesta_exception
    if real_exception is not None:
        if isinstance(real_exception, WorkerExceptionWrapper):
            is_worker_exc = True
            trace = real_exception.worker_exc_traceback
            real_exception = real_exception.worker_exception
        else:
            trace = traceback.format_exc()
    else:
        trace = None

    # If the HTML status is None, use the one provide by the vesta exception
    if html_status is None:
        html_status = vesta_exc_instance.get_html_status(real_exception)

    # If the status response is None use the one provide by httplib
    if html_status_response is None:
        html_status_response = httplib.responses[html_status]
    # Else, check if html_status_response already contains the HTML status code
    else:
        match = re.search("^([0-9]*):? *(.*)$", html_status_response)
        if match and match.group(1) == str(html_status):
            # In which case it is removed from the response
            html_status_response = match.group(2)

    # If the vesta exception provide a generic message it will be used in place
    # of the specific message given here
    get_g_msg = vesta_exc_instance.get_generic_message
    generic_vesta_exc_message = get_g_msg(real_exception)
    if generic_vesta_exc_message is not None:
        vesta_exc_message = generic_vesta_exc_message
    elif real_exception:
        vesta_exc_message = unicode(real_exception)
    else:
        vesta_exc_message = u''

    # Retrieve exception context from the traceback
    if trace is not None:
        tb_list = trace.split('\n')
        if len(tb_list) > 2:
            tb_list.reverse()
            exc_context_line = 3

            # In RETRY case, the raise context is always inside celery
            # So jump to the next stack location to get the retry context
            if tb_list[exc_context_line].find('celery/app/task.py') > 0:
                exc_context_line += 2

            # From there get the first line matching File *, line *, in *
            match = None
            while match is None and exc_context_line < len(tb_list):
                match = re.match(' *File "(.*)", line ([0-9]+), in (.*)',
                                 tb_list[exc_context_line])
                if match is None:
                    exc_context_line += 1
                    continue

                filename = path.basename(match.group(1))
                line = match.group(2)
                fct = match.group(3)
                exc_context = u'{file}:{line} in {fct}'.format(file=filename,
                                                               line=line,
                                                               fct=fct)
                vesta_exc_message += u' [{0}]'.format(exc_context)

    get_x_code = vesta_exc_instance.get_exception_code
    vesta_exception_code = get_x_code(real_exception)

    html_response_header = (u'{status} : {resp}'
                            .format(status=html_status,
                                    resp=html_status_response))

    if real_exception is not None:
        vesta_exc_log_msg = (u'{code} : {info}'
                             .format(code=vesta_exception_code,
                                     info=vesta_exc_message))
        logger.info(u'The following exception has been raised : '
                    u'{{{type}}} : {msg}'
                    .format(type=type(real_exception).__name__,
                            msg=unicode(real_exception)))
    else:
        vesta_exc_log_msg = ''

    logger.info(u'An error response is returned to the request {req} :'
                u' {resp}'
                .format(req=request.url,
                        resp=u'[{html_resp}] {vesta_exc}'
                        .format(html_resp=html_response_header,
                                vesta_exc=vesta_exc_log_msg)))

    if request_wants_json():
        # Line break doesn't make sense in json
        vesta_exc_message = vesta_exc_message.replace(u"\\n", u" ")
        # Replace double quote by single one because json uses double quotes
        vesta_exc_message = vesta_exc_message.replace(u'"', u"'")

        if is_worker_exc:
            status_response = {
                'uuid': vesta_exception.task_uuid,
                'status': vesta_exception.task_status,
                'result': {
                    'code': vesta_exception_code,
                    'message': vesta_exc_message
                }
            }
            # Worker exceptions have a FAILURE status in the body but are sent
            # as a 200 response
            return jsonify(status_response), 200
        else:
            response = {
                'status': html_status,
                'description': html_status_response,
                'vesta': {
                    'code': vesta_exception_code,
                    'message': vesta_exc_message
                }
            }
            return jsonify(response), html_status
    else:
        # Escapes message properly for HTML
        html_escape_table = {
            u'&': u'&amp;',
            u'"': u'&quot;',
            u"'": u'&apos;',
            u'>': u'&gt;',
            u'<': u'&lt;'
        }
        vesta_exc_log_msg = u''.join(html_escape_table.get(c, c) for c
                                     in vesta_exc_log_msg)

        # Replace break line by the HTML <br> symbol
        vesta_exc_log_msg = vesta_exc_log_msg.replace('\n', '<br>')

        # The Markup function tells jinja to not escape the string
        # (use it as is)
        vesta_exc_log_msg = Markup(vesta_exc_log_msg)

        doc_url = 'http://{0}/doc'.format(APP.config['MY_SERVER_NAME'])

        if real_exception is not None:
            template = render_template('error.html',
                                       html_response=html_response_header,
                                       vesta_exception=vesta_exc_log_msg,
                                       doc_url=doc_url)
        else:
            template = render_template('error.html',
                                       html_response=html_response_header,
                                       doc_url=doc_url)
        return template, html_status


# ---------------------------------------------------------------------------
def get_requests_db():
    return get_db('Requests')


# ---------------------------------------------------------------------------
def get_invocations_db():
    return get_db('Invocations')


# ---------------------------------------------------------------------------
def get_db(name):
    """
    Get a connection to an existing database. If it does not exist, create a
    connection to local sqlite3 file.

    If the local sqlite3 file doesn't exist, init it using a schema.
    """
    logger = logging.getLogger(__name__)
    database = getattr(g, '_{0}_database'.format(name), None)
    if database is None:
        d_fn = APP.config['DATABASES'][name]['filename']
        database_fn = None
        if path.isabs(d_fn):
            database_fn = d_fn
        else:
            database_fn = path.join(APP.root_path, d_fn)

        logger.debug(u"Using db filename : {0}".format(database_fn))
        if not path.exists(database_fn):
            database = g._database = sqlite3.connect(database_fn)
            init_db(database, name)
        else:
            database = g._database = sqlite3.connect(database_fn)

    return database


def init_db(database, name):
    """
    Initialize a database from a schema
    """
    logger = logging.getLogger(__name__)
    logger.info(u"Initializing {0} database".format(name))
    with current_app.app_context():
        dbs_fn = APP.config['DATABASES'][name]['schema_filename']
        schema_fn = None
        if path.isabs(dbs_fn):
            schema_fn = dbs_fn
        else:
            schema_fn = path.join(APP.root_path, dbs_fn)

        logger.debug(u"Using schema filename : {0}".format(schema_fn))
        with current_app.open_resource(schema_fn, mode='r') as schema_f:
            database.cursor().executescript(schema_f.read())
        database.commit()


def log_request(service_name, url):
    """
    Log an invocation into the DB

    :param service_name: service to which a request has been made
    :param url: URL used to access API
    """
    logger = logging.getLogger(__name__)
    query = 'insert into invocations values(CURRENT_TIMESTAMP, ?, ?, ?)'

    logger.info(u"Log into DB : {0}".format(query))

    database = get_invocations_db()
    cur = database.execute(query, [service_name, request.remote_addr, url])
    cur.close()
    database.commit()


class AnyIntConverter(BaseConverter):
    """
    Matches one of the items provided.

    Items must be integer and comma separated with space
    to avoid confusion with floating point value in the parser

    Ex.: 1, 2, 3
    And not 1,2,3 because it will parse as float 1,2 and 3
    """

    def __init__(self, mapping, *items):
        BaseConverter.__init__(self, mapping)
        # Start by enforcing that x is an integer then convert it to string
        self.regex = '(?:%s)' % '|'.join([str(int(x)) for x in items])
