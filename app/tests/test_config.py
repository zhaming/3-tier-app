#coding:utf-8
import unittest
import mock
import tempfile
import shutil
import os

import scalr


class TestConnectionInfoParser(unittest.TestCase):
    """
    Test that the parser looks at the correct files and reads the values
    """
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_valid_config(self):
        for fname, attr in scalr.ConnectionInfo.CONFIG_STRUCTURE:
            with open(os.path.join(self.test_dir, fname), 'w') as f:
                f.write(fname)

        conf = scalr.ConnectionInfo(self.test_dir)

        for fname, attr in scalr.ConnectionInfo.CONFIG_STRUCTURE:
            self.assertEqual(getattr(conf, attr), fname)


class TestDBConnectionInformation(unittest.TestCase):
    def setUp(self):
        self.username = 'uname'
        self.password = 'password'
        self.master = 'master.example.com'
        self.slave = 'slave.example.com'

        self.master_conn_info = scalr.DBConnectionInformation(
            self.master, self.username, self.password, True)

        self.slave_conn_info = scalr.DBConnectionInformation(
            self.slave, self.username, self.password, False)

    def test_get_ips(self):
        """
        Test our IP lookups
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
