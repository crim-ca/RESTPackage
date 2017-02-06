#!/usr/bin/env python
# coding:utf-8

"""
Unit tests for API framework
"""

# -- Standard lib -------------------------------------------------------------
from unittest import TestCase
from logging import getLogger
import tempfile
import os

# -- Project -----------------------------------------------------------------
from VestaRestPackage.app_objects import APP


class VRPTestCase(TestCase):

    def setUp(self):
        self.logger = getLogger(__name__)

        self.db_fd, APP.config['DATABASE'] = tempfile.mkstemp()
        APP.config['TESTING'] = True
        APP.config['SERVER_NAME'] = 'localhost'

        APP.config["WORKER_SERVICES"] = {
            'my_service': {
                # Keyword used in the rest API to access this service
                # (ex.: http://server/<route_keyword>/info)
                # Set to '.' to access this service without keyword
                # (ex.: http://server/info)
                'route_keyword': 'my_service',

                # The celery task name.
                # Must match the task in the worker APP name :
                # <proj_name>.<task_name>
                # (ex.: worker.my_service)
                'celery_task_name': 'my_service',

                # The celery queue name.
                # Must match the queue name specified when starting the worker
                # (by the -Q switch)
                'celery_queue_name': 'my_service_0.1.0',

                # Following parameters are required by the CANARIE API (info
                # request)
                'name': 'My service',
                'synopsis': "RESTful service providing my_service.",
                'version': "0.1.0",  # Expected version - will check.
                'institution': 'My Organisation',
                'releaseTime': '2015-01-01T00:00:00Z',
                'supportEmail': 'support@my-organisation.ca',
                'category': "Data Manipulation",
                'researchSubject': "My research subject",
                'tags': "my_service, research",

                # The following parameters are used to respond to some CANARIE
                # API request.
                #
                # They must be one of the following:
                #  - A valid URL to perform a redirection
                #  - A relative template file that will be used to generate the
                #    html page (relative to the templates directory)
                #  - A response string and the html status separated by a comma
                #  that will be used  to make a response to the requested
                #  element. Ex.: 'Not available,404'

                'home': "http://www.google.com",
                'doc': "http://www.google.com",
                'releasenotes': "http://www.google.com",
                'support': "http://www.google.com",

                # If the source are not provided, CANARIE requires a 204 (No
                # content) response
                'source': ",204",
                'tryme': "http://www.google.com",
                'licence': "http://www.google.com",
                'provenance': "http://www.google.com",
                'os_args': {'image': 'my_service_image_name_v_0.1.0',
                            'instance_type': 'm1.large'},
                # Process-request to spawn VM ratio
                'rubber_params': {'spawn_ratio': 0.1}
                }
        }
        self.app = APP.test_client()
        # with APP.app_context():
        #     flaskr.init_db()

    def tearDown(self):
        os.close(self.db_fd)
        os.unlink(APP.config['DATABASE'])

    def test_db_files(self):
        db_fn = APP.config['DATABASES']['Invocations']['schema_filename']
        self.assertTrue(os.path.exists(db_fn))
        db_fn = APP.config['DATABASES']['Requests']['schema_filename']
        self.assertTrue(os.path.exists(db_fn))

    def test_stats(self):
        # Inject header so we can request JSON
        headers = {'Content-Type': "application/json"}
        rv = self.app.get('/my_service/stats', headers=headers)
        self.logger.debug('Return value %s', rv.data)
        # Validate that we got the right structure
        self.assertEqual(rv.status_code, 200)

    def test_general_info(self):
        # Inject header so we can request JSON
        headers = {'Content-Type': "application/json"}
        rv = self.app.get('/info', headers=headers)
        self.logger.debug('Return value %s', rv.data)
        # Validate that we got the right structure
        self.assertEqual(rv.status_code, 200)

    # def test_service_info(self):
    #     # Need access to AMQP so this test is deactivated for now.
    #     # Inject header so we can request JSON
    #     headers = {'Content-Type': "application/json"}
    #     rv = self.app.get('/my_service/info', headers=headers)
    #     self.logger.debug('Return value %s', rv.data)
    #     # Validate that we got the right structure
    #     self.assertEqual(rv.status_code, 200)

    def test_doc(self):
        headers = {'Content-Type': "application/json"}
        rv = self.app.get('/my_service/doc', headers=headers)
        self.logger.debug('Return value %s', rv.data)
        # Validate that we got the right structure
        self.assertEqual(rv.status_code, 302)

    def test_releasenotes(self):
        headers = {'Content-Type': "application/json"}
        rv = self.app.get('/my_service/releasenotes', headers=headers)
        self.logger.debug('Return value %s', rv.data)
        # Validate that we got the right structure
        self.assertEqual(rv.status_code, 302)

    def test_support(self):
        headers = {'Content-Type': "application/json"}
        rv = self.app.get('/my_service/support', headers=headers)
        self.logger.debug('Return value %s', rv.data)
        # Validate that we got the right structure
        self.assertEqual(rv.status_code, 302)

    def test_source(self):
        headers = {'Content-Type': "application/json"}
        rv = self.app.get('/my_service/source', headers=headers)
        self.logger.debug('Return value %s', rv.data)
        # Validate that we got the right structure
        self.assertEqual(rv.status_code, 204)

    def test_tryme(self):
        headers = {'Content-Type': "application/json"}
        rv = self.app.get('/my_service/tryme', headers=headers)
        self.logger.debug('Return value %s', rv.data)
        # Validate that we got the right structure
        self.assertEqual(rv.status_code, 302)

    def test_licence(self):
        headers = {'Content-Type': "application/json"}
        rv = self.app.get('/my_service/licence', headers=headers)
        self.logger.debug('Return value %s', rv.data)
        # Validate that we got the right structure
        self.assertEqual(rv.status_code, 302)

    def test_provenance(self):
        headers = {'Content-Type': "application/json"}
        rv = self.app.get('/my_service/provenance', headers=headers)
        self.logger.debug('Return value %s', rv.data)
        # Validate that we got the right structure
        self.assertEqual(rv.status_code, 302)
