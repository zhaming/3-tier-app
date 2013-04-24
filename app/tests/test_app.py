#coding:utf-8
import unittest
import mock
import copy
import warnings

import MySQLdb

import scalr
from scalr import db
from scalr import exceptions

TEST_DB_CONFIG = {
    '_master': 'localhost',
    '_slave': 'localhost',
    'username': 'root',
    'password': 'APP_TEST_PASSWORD'
}


class AppTestCase(unittest.TestCase):
    def setUp(self):
        # Set the app client up
        scalr.app.config['TESTING'] = True
        self.client = scalr.app.test_client()

        # Set the database up
        self.db_config = copy.copy(TEST_DB_CONFIG)
        self.parser_patcher = mock.patch('scalr.config.parse_config')
        self.parser = self.parser_patcher.start()
        self.parser.side_effect = self.get_db_config

        # Ignore DB warnings
        warnings.filterwarnings('ignore', category=MySQLdb.Warning)

    def tearDown(self):
        self.parser_patcher.stop()
        warnings.resetwarnings()

    def get_db_config(self, _):
        """
        We use this method to let test methods override the DB config in
        realtime
        We need to accept a path argument (the app will pass one to us),
        we ignore it.
        """
        return db.ConnectionInfo(**self.db_config)


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

        r = self.client.post('/', data = {'value': insert})
        self.assertEqual(r.status_code, 302)

        r = self.client.get('/')
        self.assertIn(insert, r.data)
        
    def test_read_error(self):
        """
        Check that we notify the user of read errors
        """
        self.db_config['_slave'] = "blah"

        r = self.client.get('/')
        self.assertIn('Error', r.data)

    def test_write_error(self):
        self.db_config['_master'] = "blah"

        r = self.client.post('/', data = {'value':'myValue'})
        self.assertIn('Error', r.data)

    def test_no_config(self):
        self.parser.side_effect = exceptions.NoConnectionInfo

        r = self.client.get('/')
        self.assertIn('Missing Database Connection Info', r.data)
