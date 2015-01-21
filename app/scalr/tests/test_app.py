#coding:utf-8
from __future__ import unicode_literals
import os
import warnings
import unittest

import pymysql

import scalr
from scalr import config

from scalr.tests import TEST_DB_CONFIG


class BaseAppTestCase(unittest.TestCase):
    def setUp(self):
        # Set the app client up
        scalr.app.config['TESTING'] = True
        self.client = scalr.app.test_client()

        # Set environment up
        for k, v in config.ENV_CONFIG_STRUCTURE:
            os.environ[k] = TEST_DB_CONFIG[v]

        # Ignore DB warnings
        warnings.filterwarnings('ignore', category=pymysql.Warning)

    def tearDown(self):
        for k, _ in config.ENV_CONFIG_STRUCTURE:
            try:
                del os.environ[k]
            except KeyError:
                pass

        warnings.resetwarnings()


class AppTestCase(BaseAppTestCase):
    def test_get(self):
        """
        Check that we render the page correctly
        """
        r = self.client.get('/')
        self.assertEqual(r.status_code, 200)

    def test_post(self):
        """
        Check that we can submit values
        """
        insert = 'myValue'

        r = self.client.post('/', data={'value': insert})
        self.assertEqual(r.status_code, 302)

        r = self.client.get('/')
        self.assertIn(insert, r.data.decode('utf-8'))

    def test_read_error(self):
        """
        Check that we notify the user of read errors
        """
        os.environ['APP_MYSQL_SLAVE'] = "blah"

        r = self.client.get('/')
        self.assertIn('An error occurred when', r.data.decode('utf-8'))

    def test_write_error(self):
        """
        Check that we notify the user of write errors
        """
        os.environ['APP_MYSQL_MASTER'] = "blah"

        r = self.client.post('/', data={'value': 'myValue'})
        self.assertIn('An error occurred when', r.data.decode('utf-8'))

    def test_no_config(self):
        """
        Check that we report an absent configuration
        """
        del os.environ['APP_MYSQL_MASTER']

        r = self.client.get('/')
        self.assertIn('Something looks wrong', r.data.decode('utf-8'))
