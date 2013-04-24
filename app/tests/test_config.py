#coding:utf-8
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

        for fname, attr in config.CONFIG_STRUCTURE:
            with open(os.path.join(self.test_dir, fname), 'w') as f:
                f.write(fname)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_valid_config(self):
        """
        Check that a valid config gets parsed correctly
        """
        conf = config.parse_config(self.test_dir)

        for fname, attr in config.CONFIG_STRUCTURE:
            self.assertEqual(getattr(conf, attr), fname)

    def test_invalid_config(self):
        """
        Check that we handle invalid configs
        """
        self.assertRaises(exceptions.NoConnectionInfo, config.parse_config, '/wrongpath')

    def test_to_db_connection(self):
        """
        Check that config info interacts well with DB info
        """
        self.conn_info = config.parse_config(self.test_dir)

        def replicating(x):
            if x == 'mysql-master':
                return [x, [], ['10.0.0.1']]
            else:
                return [x, [], ['10.0.0.2', '10.0.0.3']]

        with mock.patch('socket.gethostbyname_ex') as gethostbyname_ex:


            # No replication
            gethostbyname_ex.return_value = ['example.com', [], ['10.0.0.1']]
            self.assertEqual(self.conn_info.master.ips(), self.conn_info.slave.ips())
            self.assert_(not self.conn_info.replicating())

            # Replication
            gethostbyname_ex.return_value = None
            gethostbyname_ex.side_effect = replicating
            self.assertNotEqual(self.conn_info.master.ips(), self.conn_info.slave.ips())
            self.assert_(self.conn_info.replicating())


class DBConnectionInfoTestCase(unittest.TestCase):
    def setUp(self):
        self.username = 'uname'
        self.password = 'password'
        self.master = 'master.example.com'
        self.slave = 'slave.example.com'

        self.master_conn_info = db.DBConnection(
            self.master, self.username, self.password, True)

        self.slave_conn_info = db.DBConnection(
            self.slave, self.username, self.password, False)

    def test_get_ips(self):
        """
        Check that we do the correct IP lookups
        """
        master_ips = ['10.0.0.1']
        master_lookup = (self.master, [], master_ips)
        slave_ips = ['10.0.0.2', '10.0.0.3']
        slave_lookup = (self.slave, [], slave_ips)

        with mock.patch('socket.gethostbyname_ex') as gethostbyname_ex:
            # Test lookups that work
            gethostbyname_ex.return_value = master_lookup
            self.assertEqual(master_ips, self.master_conn_info.ips())

            gethostbyname_ex.return_value = slave_lookup
            self.assertEqual(slave_ips, self.slave_conn_info.ips())

            import socket
            error_message = '[Errno 8] nodename nor servname provided, or not known'
            gethostbyname_ex.side_effect = socket.gaierror(8, error_message)
            self.assertEqual(1, len(self.master_conn_info.ips()))
            self.assertIn(error_message, self.master_conn_info.ips()[0])
