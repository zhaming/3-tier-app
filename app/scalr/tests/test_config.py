#coding:utf-8
from __future__ import unicode_literals
import unittest
import mock
import tempfile
import shutil
import os

import scalr
from scalr import exceptions
from scalr import db
from scalr import config


class ConnectionInfoParserTestCase(unittest.TestCase):
    """
    Test that the parser looks at the correct files and reads the values
    """
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

        for fname, attr in config.FILE_CONFIG_STRUCTURE:
            with open(os.path.join(self.test_dir, fname), 'w') as f:
                f.write(fname)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_valid_config(self):
        """
        Check that a valid config gets parsed correctly
        """
        conf = config.parse_config(self.test_dir)

        for fname, attr in config.FILE_CONFIG_STRUCTURE:
            self.assertEqual(getattr(conf, attr), fname)

    def test_invalid_config(self):
        """
        Check that we handle invalid configs
        """
        self.assertEqual(None, config.parse_config('/wrongpath'))

    def test_to_db_connection(self):
        """
        Check that config info interacts well with DB info
        """
        conn_info = config.parse_config(self.test_dir)
        self.assertEqual("mysql-master", conn_info.master_ip)
        self.assertEqual("mysql-slave", conn_info.slave_ip)
        self.assertEqual(["mysql-slave"], conn_info.slave_ips)
        self.assertEqual("mysql-username", conn_info.username)
        self.assertEqual("mysql-password", conn_info.password)


class DBConnectionInfoTestCase(unittest.TestCase):
    def setUp(self):
        self.username = 'uname'
        self.password = 'password'
        self.master = '10.10.0.1'
        self.slaves = '10.10.0.2\n10.10.0.3'
        self.slave_ips = self.slaves.split()

    def test_conn_master(self):
        conn_info = db.ConnectionInfo(self.username, self.password, self.master, [])

        self.assertEqual(self.master, conn_info.master_ip)
        self.assertEqual(self.master, conn_info.slave_ip)
        self.assertEqual([self.master], conn_info.slave_ips)
        self.assertFalse(conn_info.replicating())

    def test_conn_slave(self):
        conn_info = db.ConnectionInfo(self.username, self.password, self.master, self.slaves)

        self.assertEqual(self.master, conn_info.master_ip)
        self.assertIn(conn_info.slave_ip, self.slave_ips)
        self.assertEqual(self.slave_ips, conn_info.slave_ips)
        self.assertTrue(conn_info.replicating())
