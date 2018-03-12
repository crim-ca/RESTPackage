"""
Run process in blocking mode. Check and return results on stdout.
"""

from logging.config import fileConfig
from argparse import ArgumentParser
from time import time as timer
from logging import getLogger
from urlparse import urljoin
from time import sleep
import json
from os.path import abspath, dirname, join

import requests

from .jwt_ import generate_token
from .app_objects import APP

SUCCESS_WAIT_ITER_TIME = 1
THIS_DIR = abspath(dirname(__file__))
SG_URL = "http://{s}".format(s=APP.config['MY_SERVER_NAME'])

class ServerError(Exception):
    """Indicates that the remote server could not complete the request"""
    pass

class TimeOutError(Exception):
    """Indicates that the remote server could not complete
    the request on time."""
    pass

def get_header():
    """
    Generate header according to security configuration.
    """
    logger = getLogger(__name__)

    if not APP.config['SECURITY'].get('BYPASS_SECURITY', False):
        logger.info("Getting token")
        signature_key = APP.config['SECURITY']['JWT']['JWT_SIGNATURE_KEY']
        audience = APP.config['SECURITY']['JWT']['JWT_AUDIENCE']
        algorithm = APP.config['SECURITY']['JWT']['JWT_ALGORITHM']
        token = generate_token(signature_key, audience, algorithm,
                               duration=600)

        header = {"content-type": 'application/json',
                  "Authorization": token}
    else:
        header = {"content-type": 'application/json'}
    return header


# -- Annotator ---------------------------------------------------------------
def annotate_url(service_name, url, params):
    """
    Run tests for a given service.
    """
    logger = getLogger(__name__)
    logger.info("Running tests for %s", service_name)
    logger.info("ServiceGateway address is %s", SG_URL)
    logger.debug("Params are : %s", params)

    header = get_header()

    params['doc_url'] = url
    resp = requests.post("{u}/{s}/annotate".format(u=SG_URL, s=service_name),
                headers=header,
                params=params)
    logger.info("POST to annotate response : %s", resp)
    logger.info("POST to annotate body: %s", resp.text)
    resp.raise_for_status()
    resp_json = resp.json()
    uuid = resp_json['uuid']
    logger.info("Annotation UUID: %s", uuid)
    return uuid


def annotate(service_name, params):
    """
    Run tests for a given service.
    The url of the document to annotate is in the params
    """
    logger = getLogger(__name__)
    logger.info("Running tests for %s", service_name)
    logger.info("ServiceGateway address is %s", SG_URL)
    logger.debug("Params are : %s", params)

    header = get_header()

    resp = requests.post("{u}/{s}/annotate".format(u=SG_URL, s=service_name),
                headers=header,
                params=params)
    logger.info("POST to annotate response : %s", resp)
    logger.info("POST to annotate body: %s", resp.text)
    resp.raise_for_status()
    resp_json = resp.json()
    uuid = resp_json['uuid']
    logger.info("Annotation UUID: %s", uuid)
    return uuid


def annotate_service(service_name, storage_doc_id, params):
    """
    Run tests for a given service.
    """
    logger = getLogger(__name__)
    logger.info("Running tests for %s", service_name)
    logger.info("ServiceGateway address is %s", SG_URL)
    logger.debug("Params are : %s", params)

    header = get_header()

    resp = requests.post("{u}/{s}/annotate/{d}".
                format(u=SG_URL,
                       s=service_name,
                       d=storage_doc_id),
                headers=header,
                params=params)

    logger.debug("POST request URL: %s", resp.url)
    logger.info("POST to annotation document response : %s", resp)
    logger.info("POST to annotation document body: %s", resp.text)
    resp.raise_for_status()
    resp_json = resp.json()
    uuid = resp_json['uuid']
    logger.info("Annotation UUID: %s", uuid)
    return uuid


def process_url(service_name, url, params, json={}, sg_url=SG_URL):
    """
    Run tests for a given service.
    """
    logger = getLogger(__name__)
    logger.info("Running process tests for %s", service_name)
    logger.info("ServiceGateway address is %s", sg_url)
    logger.debug("Params are : %s", params)

    header = get_header()

    params['doc_url'] = url
    resp = requests.post("{u}/{s}/process".format(u=sg_url, s=service_name),
                headers=header,
                params=params,
                json=json)
    logger.info("POST to process response : %s", resp)
    logger.info("POST to process body: %s", resp.text)
    resp.raise_for_status()
    resp_json = resp.json()
    uuid = resp_json['uuid']
    logger.info("Annotation UUID: %s", uuid)
    return uuid


def process_service(service_name, storage_doc_id, params, json={'a': 42}):
    """
    Run tests for a given service.
    """
    logger = getLogger(__name__)
    logger.info("Running tests for %s", service_name)
    logger.info("ServiceGateway address is %s", SG_URL)
    logger.info("Getting token")
    logger.debug("Params are : %s", params)

    header = get_header()

    resp = requests.post("{u}/{s}/process/{d}".
                format(u=SG_URL,
                       s=service_name,
                       d=storage_doc_id),
                headers=header,
                params=params,
                json=json)
    logger.debug("POST request URL: %s", resp.url)
    logger.info("POST to process document response : %s", resp)
    logger.info("POST to process document body: %s", resp.text)
    resp.raise_for_status()
    resp_json = resp.json()
    uuid = resp_json['uuid']
    logger.info("Annotation UUID: %s", uuid)
    return uuid


def get_result(worker_name, uuid, timeout=None, sg_url=SG_URL):
    """
    Wait for processing results and return RAW data structure.

    :param timeout: How many seconds to wait for a result.
    :param worker_name: name of the worker
    :param uuid: UUID of the task
    :param sg_url: URL of the service gateway
    """
    logger = getLogger(__name__)
    status = None
    logger.info("Getting result of processing request %s for %s",
                uuid, worker_name)
    status_url = urljoin(sg_url, "{}/status".format(worker_name))
    logger.debug("Status URL is %s", status_url)
    starttime = timer()
    logger.debug("Started at %s", starttime)
    if timeout:
        timeout = int(timeout)
        logger.info("Using %s as timeout value", timeout)
    while status != 'SUCCESS':
        logger.info("Waiting for success state")
        sleep(SUCCESS_WAIT_ITER_TIME)
        r_val = requests.get(status_url, params={'uuid': uuid})
        if r_val.status_code != 502:  # Ignore Bad gateway return codes...
            r_val.raise_for_status()
        else:
            logger.warning("BAD gateway response: %s", r_val)
        status = r_val.json()['status']
        logger.debug(r_val.text)
        logger.info("Status is %s", status)
        if status == "FAILURE":
            raise ServerError("Error: Remote server says: {}".
                              format(r_val.json()['result']['message']))
        elif status == "PROGRESS":
            progress = r_val.json()['result']['current']
            logger.info("Progress stated at %s%%", progress)
        elif status in ['EXPIRED', 'REVOKED']:
            raise ServerError("Error with task status: Contact administrator")

        latency = int(timer() - starttime)
        logger.info("Current latency is %s", latency)
        if latency > timeout:
            raise TimeOutError("Process did not succeed in required time")

    status_result = r_val.json()
    logger.debug("Result string is %s", status_result)
    return status_result


def todict_str(x):
    return x.split('=')[0], x.split('=')[1]


def main():
    """
    Command line entry point to run a service in blocking mode
    """
    log_conf_fn = join(THIS_DIR, 'logging.ini')
    parser = ArgumentParser(description=__doc__)
    parser.add_argument("service_name",
                        help="Name of the service to call on the SG")
    parser.add_argument("doc_url",
                        help="URL of the document to process")
    parser.add_argument("--json",
                        help="Path to a file containing the parameters to "
                             "submit to the service as body contents.")
    parser.add_argument("--json_string",
                        help="String containing the parameters to "
                             "submit to the service as body contents.")
    parser.add_argument("--sg_url",
                        help="HTTP URL base path for the SG",
                        default=SG_URL)
    parser.add_argument("--params", nargs='+', default={},
                        help="Additionnal parameters to pass in url"
                             " parameters with syntax a=x")
    parser.add_argument("--timeout",
                        help="Timeout expressed in seconds for result.")
    parser.add_argument("-l",
                        action='store',
                        default=log_conf_fn,
                        dest='logging_conf_fn',
                        help='Set logging configuration filename')

    args = parser.parse_args()
    fileConfig(args.logging_conf_fn)
    if args.json:
        with open(args.json, "rt") as params_file:
            json_contents = json.load(params_file)
    elif args.json_string:
        json_contents = json.loads(args.json_string)
    else:
        json_contents = None
    if args.params:
        params = dict([todict_str(e) for e in args.params])
    else:
        params = args.params
    uuid = process_url(args.service_name,
                       args.doc_url,
                       params,
                       json_contents,
                       args.sg_url)
    result = get_result(args.service_name, uuid, args.timeout, args.sg_url)
    print(result)

if __name__ == '__main__':
    main()
