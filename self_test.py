#!/usr/bin/env python
# coding:utf-8

"""
Unit tests for API framework
"""

# -- Standard lib ------------------------------------------------------------
import httplib
import json
import time
import re
import os

# -- third - party -----------------------------------------------------------
from flask import render_template
import requests


SSM_SERVER = 'services.vesta.crim.ca'
SSM_REST_ROOT = '/multimedia_storage/v1_5'

# VLB_SERVER = 'services.vesta.crim.ca'
VLB_SERVER = 'localhost'
VLB_REST_ROOT = '/vlb/v1_5/transition'

test_filename = '/media/sf_develop/vesta/trunk/Service_Storage_Multimedia/' \
                'Service_Streaming/MIT_short.mp4'


class Code:
    def __init__(self):
        pass

    CAUSE_ERROR = 1


class ResultList(list):
    def __init__(self):
        super(ResultList, self).__init__()

    def append(self, obj):
        if len(obj) != 8:
            raise Exception("Bad tuple size : Requires 7 elements")

        super(ResultList, self).append(obj)

        if obj[6] == "error":
            test_result = "FAIL"
        else:
            test_result = " OK "
        res = "{res} {method} on {server}{rest_root}{url} " \
              "[{type}] -> {status} : {reason}"\
              .format(res=test_result,
                      method=obj[3],
                      server=obj[0],
                      rest_root=obj[1],
                      url=obj[2],
                      type=obj[4],
                      status=obj[5],
                      reason=obj[7])
        print res


def escape(my_string):
    """
    Escape characters that should not be treated as regex
    symbols

    :param my_string: Sequence which will be escaped.
    :type my_string: string
    """
    regex_symbols = ('\\', '^', '[', ']', '.', '$', '{', '}', '*', '(', ')',
                     '+', '|', '?')
    for sym in regex_symbols:
        my_string = my_string.replace(sym, '\\' + sym)
    return my_string


def test(result, server, rest_root, url, io_types,
         method='GET',
         response_status=httplib.OK,
         regex='.*'):

    conn = httplib.HTTPConnection(server)
    oriurl = url
    url = rest_root + url
    out = ()
    for io_type in io_types:
        body = None
        if not io_type:
            headers = {"Accept": "*/*"}
        else:
            headers = {"Accept": io_type}
        conn.request(method, url, body, headers)

        reason = None
        response = conn.getresponse()

        redirect_count = 0
        while redirect_count < 10 and (response.status == 302):  # redirect
            content_location = response.getheader('Location')
            body = response.read()

            match = re.search('^(.*://)?([^/]+)(/.*)$', content_location)
            if match:
                protocol = match.group(1)
                server = match.group(2)
                redir_url = match.group(3)
                if protocol.find('https') > -1:
                    redir_conn = httplib.HTTPSConnection(server)
                else:
                    redir_conn = httplib.HTTPConnection(server)
                if not headers:
                    redir_conn.request(method, redir_url)
                else:
                    redir_conn.request(method, redir_url, body, headers)
                response = redir_conn.getresponse()
                redirect_count += 1

        body = response.read()
        if response.status == response_status:
            content_type = response.getheader('Content-Type')

            if io_types[io_type]:
                if content_type is not None and\
                   content_type.find(io_types[io_type]) >= 0:

                    if regex != ".*":
                        # For response of type xml or html escape properly some
                        # symbols
                        if re.search("(xml|html)", content_type):
                            escaped_regex = (regex.replace("&", "&amp;").
                                             replace("<", "&lt;").
                                             replace(">", "&gt;").
                                             replace("'", "&#39;").
                                             replace('"', "&quot;"))
                        else:
                            escaped_regex = regex

                        comp = re.compile(escaped_regex,
                                          re.MULTILINE | re.DOTALL)
                        match = comp.search(body)
                        if not match:
                            reason = "response doesn't contain the required"\
                                     " content : " + regex + ", get : "\
                                     + str(body)
                else:
                    reason = "bad response type : want " + io_types[io_type] +\
                             ", get " + str(content_type)
        else:
            reason = "bad response status : want " + str(response_status) +\
                     ", get " + str(response.status) + " : " + str(body)

        if not io_type:
            io_type = "default"

        if not reason:
            result_tuple = (server, rest_root, oriurl, method, io_type,
                            response_status, "succeed", "passed")
        else:
            # On failure body is not returned
            body = None
            result_tuple = (server, rest_root, oriurl, method, io_type,
                            response_status, "error", reason)
        result.append(result_tuple)
        out = out + (body, )
    return out


def monitor_status(result, server, rest_root, task_uuid,
                   wanted_status='SUCCESS'):
    task_status = 'PENDING'
    progress = None
    final_state = ['REVOKED', 'SUCCESS', 'FAILURE']

    json_type = 'application/json'
    test_json_type = {json_type: json_type}
    resp_json = None
    got_same_progress = False

    status_monitoring_freq = 5
    status_monitoring_when_no_prog_freq = 30

    # Request status until a final state or if no progress is detected
    while task_status not in final_state:
        # Give a chance to the task to do some progress
        time.sleep(status_monitoring_freq)

        resp = test(result, server, rest_root,
                    "/status?uuid={uuid}".format(uuid=task_uuid),
                    test_json_type)
        if not resp[0]:
            print "status request failed (quit monitoring)"
            break
        resp_json = json.loads(resp[0])
        task_status = resp_json['status']
        if task_status == 'PROGRESS':
            try:
                new_progress = resp_json['result']['current']
            except KeyError:
                result_tuple = (server,
                                rest_root,
                                "/status?uuid={uuid}".format(uuid=task_uuid),
                                'GET',
                                json_type,
                                httplib.OK,
                                'error',
                                'bad result progress : {0}'
                                .format(str(resp_json)))
                result.append(result_tuple)

                print "status result doesn't contains progress " \
                      "(quit monitoring) : {0}".format(resp_json)
                break

        else:
            new_progress = task_status
        if new_progress == progress:
            # If the same progress is obtain twice stop monitoring
            # We conclude that the task is stalled
            if got_same_progress:
                result_tuple = (server,
                                rest_root,
                                "/status?uuid={uuid}".format(uuid=task_uuid),
                                'GET',
                                json_type,
                                httplib.OK,
                                'error',
                                'no more progress')
                result.append(result_tuple)
                wait_time = status_monitoring_when_no_prog_freq
                wait_time += 2 * status_monitoring_freq

                print "status doesn't progress for the last {interval} " \
                      "(quit monitoring) ".format(interval=wait_time)
                break
            else:
                got_same_progress = True
                # Give a chance to the task to do some progress
                time.sleep(status_monitoring_when_no_prog_freq)
        else:
            got_same_progress = False

        progress = new_progress

    if task_status != wanted_status:

        result_tuple = (server,
                        rest_root,
                        "/status?uuid={uuid}",
                        'GET',
                        json_type,
                        httplib.OK,
                        'error')
        msg = 'Status should be {0} and got {1}'.\
            format(wanted_status, task_status)

        if task_status == 'REVOKED':
            msg = msg + '. ' + resp_json['result']
        elif task_status == 'FAILURE':
            msg = msg + '. ' + resp_json['result']['message']

        result_tuple = result_tuple + (msg,)
        result.append(result_tuple)
    return resp_json


def run():
    """
    Entry point for executing tests.
    """
    result = ResultList()
    html_type = 'text/html'
    json_type = 'application/json'

    # Test canarie API
    test_html_type = {'': html_type}
    test_json_type = {json_type: json_type}
    test_both_types = {'': html_type, json_type: json_type}

    run_all = True
    run_canarie_api = False
    run_swift_post = False
    run_transcoding = False
    run_annotation = False
    run_other_get = False
    run_cancel_transcode = False
    run_cancel_annotate = False

    if run_all or run_canarie_api:
        canarie_server = [(SSM_SERVER, SSM_REST_ROOT),
                          (VLB_SERVER, VLB_REST_ROOT)]
    else:
        canarie_server = []

    for server_info in canarie_server:

        server = server_info[0]
        rest_root = server_info[1]

        test(result, server, rest_root, "/", test_html_type)
        test(result, server, rest_root, "/info", test_both_types,
             regex="(name.*synopsis.*version.*institution.*releaseTime."
             "*category.*tags|category.*institution.*name."
             "*releaseTime.*synopsis.*tags.*version)")
        test(result, server, rest_root, "/stats", test_both_types,
             regex="(lastReset.*invocations|invocations.*lastReset)")
        test(result, server, rest_root, "/doc", test_html_type)
        test(result, server, rest_root, "/releasenotes", test_html_type)
        test(result, server, rest_root, "/support", test_html_type)
        test(result, server, rest_root, "/source", {'': ''},
             response_status=httplib.NO_CONTENT,
             regex="")
        test(result, server, rest_root, "/tryme", test_html_type)
        test(result, server, rest_root, "/licence", test_html_type)
        test(result, server, rest_root, "/provenance", test_html_type)

    # Test Vesta services workflow
    #######################################################################

    # Request temp upload url
    if run_all or run_swift_post:
        resp = test(result, SSM_SERVER, SSM_REST_ROOT, "/add?filename={fn}".
                    format(fn=os.path.basename(test_filename)),
                    test_json_type)

        if resp[0] is None:
            return result

        # Upload video
        headers = {'Content-Type': 'application/octet-stream'}
        resp_json = json.loads(resp[0])
        upload_url = resp_json['upload_url']
        storage_doc_id = resp_json['storage_doc_id']
        resp = requests.put(upload_url,
                            headers=headers,
                            data=open(test_filename, 'rb'),
                            verify=False)
        result_tuple = ('ATIR',
                        '',
                        upload_url,
                        'PUT',
                        'application/octet-stream',
                        resp.status_code)

        # Doesn't work because requests.codes.ok is not valid
        # But it should ne ok according to :
        # http://docs.python-requests.org/en/latest/user/quickstart/
        # if resp.status_code != requests.codes.ok:
        if 200 <= resp.status_code < 300:
            result_tuple = result_tuple + ("succeed", "passed")
        else:
            result_tuple = result_tuple + ("error", resp.text)
        result.append(result_tuple)
    else:
        storage_doc_id = '5RVAyrGGAraAvstC7rxm3C.mp4'

    if run_all or run_transcoding:
        # Request transcoding
        resp = test(result, SSM_SERVER, SSM_REST_ROOT,
                    "/transcode/{storage_doc_id}"
                    .format(storage_doc_id=storage_doc_id),
                    test_json_type,
                    method='POST')

        if resp[0] is None:
            return result

        resp_json = json.loads(resp[0])
        task_uuid = resp_json['uuid']

        # Request status until final state
        resp_json = monitor_status(result, SSM_SERVER, SSM_REST_ROOT,
                                   task_uuid)

        if resp_json is None:
            return result

        video_annot_storage_doc_id = resp_json['result']['annot_video']
    else:
        video_annot_storage_doc_id = '3RIOqpXmpY1VxvJeUiYgsv.mp4'

    if run_all or run_annotation:
        # Request annotation
        resp = test(result, VLB_SERVER, VLB_REST_ROOT,
                    "/annotate/{storage_doc_id}"
                    .format(storage_doc_id=video_annot_storage_doc_id),
                    test_json_type,
                    method='POST')

        if resp[0] is None:
            return result

        resp_json = json.loads(resp[0])
        task_uuid = resp_json['uuid']

        # Request status until final state
        monitor_status(result, VLB_SERVER, VLB_REST_ROOT, task_uuid)

    # Test Vesta services other functions
    #######################################################################

    if run_all or run_other_get:
        # Get stream url
        test(result, SSM_SERVER, SSM_REST_ROOT,
             "/stream/{storage_doc_id}"
             .format(storage_doc_id=storage_doc_id),
             test_json_type,
             regex='.*swift.*temp_url.*')

    if run_all or run_cancel_transcode:
        # Request transcoding then cancel it
        resp = test(result, SSM_SERVER, SSM_REST_ROOT,
                    "/transcode/{storage_doc_id}"
                    .format(storage_doc_id=storage_doc_id),
                    test_json_type,
                    method='POST')

        if resp[0] is None:
            return result

        resp_json = json.loads(resp[0])
        task_uuid = resp_json['uuid']

        test(result, SSM_SERVER, SSM_REST_ROOT,
             "/cancel?uuid={uuid}".format(uuid=task_uuid),
             test_json_type)

        monitor_status(result, SSM_SERVER, SSM_REST_ROOT, task_uuid,
                       wanted_status='REVOKED')

    if run_all or run_cancel_annotate:
        # Request annotation then cancel it
        args = (result, VLB_SERVER, VLB_REST_ROOT,
                "/annotate/{storage_doc_id}"
                .format(storage_doc_id=video_annot_storage_doc_id),
                test_json_type)
        kwargs = {'method': 'POST'}

        resp = test(*args, **kwargs)
        if resp[0] is None:
            return result
        resp_json = json.loads(resp[0])
        task1_uuid = resp_json['uuid']

        resp = test(*args, **kwargs)
        if resp[0] is None:
            return result
        resp_json = json.loads(resp[0])
        task2_uuid = resp_json['uuid']

        # Cancel task2 before the 1 to make sure that it is cancel before being
        # processed, so cancelling task 1 should kill the process while
        # cancelling task 2 should prevent it from being executed
        resp = test(result, VLB_SERVER, VLB_REST_ROOT,
                    "/cancel?uuid={uuid}".format(uuid=task2_uuid),
                    test_json_type)
        resp = test(result, VLB_SERVER, VLB_REST_ROOT,
                    "/cancel?uuid={uuid}".format(uuid=task1_uuid),
                    test_json_type)
        resp_json = monitor_status(result, VLB_SERVER, VLB_REST_ROOT,
                                   task1_uuid,
                                   wanted_status='REVOKED')
        resp_json = monitor_status(result, VLB_SERVER, VLB_REST_ROOT,
                                   task2_uuid,
                                   wanted_status='REVOKED')

    # Test Vesta services errors

    # Test Vesta services unsupported methods

    return result


def test_error_code(app, test_code):

    if test_code == Code.CAUSE_ERROR:
        raise Exception("Unhandled error")
    else:
        handler = app.error_handler_spec[None].get(test_code)
        if handler is None:
            return "No handler found for error " + str(test_code)
        return handler('Error : ' + str(test_code))


def get_result():
    result = run()
    total = 0
    passed = 0
    for item in result:
        if item[7] == "passed":
            passed += 1
        total += 1

    return render_template('self_test.html', Title="Self test",
                           Result=result, Passed=passed, Total=total)

if __name__ == "__main__":
    RUN_RESULT = run()
    print RUN_RESULT
