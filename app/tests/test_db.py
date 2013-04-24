#coding:utf-8
import MySQLdb
import unittest
import warnings

import scalr


class TestDB(unittest.TestCase):
    def setUp(self):
        self.username = "root"
        self.password = "APP_TEST_PASSWORD"
        self.host = 'localhost'


class TestDBConnectionFailure(TestDB):
    def test_no_host(self):
        conn_info = scalr.DBConnectionInformation(
            'example.com', self.username, self.password, True)
        self.assertRaises(scalr.NoHost, conn_info.get_cursor)

    def test_invalid_credentials(self):
        conn_info = scalr.DBConnectionInformation(
            self.host, "invalid", self.password, True)
        self.assertRaises(scalr.InvalidCredentials, conn_info.get_cursor)

        conn_info = scalr.DBConnectionInformation(
            self.host, self.username, "invalid", True)
        self.assertRaises(scalr.InvalidCredentials, conn_info.get_cursor)


class TestDBInstructions(TestDB):


    def setUp(self):
        super(TestDBInstructions, self).setUp()

        self.master_conn_info = scalr.DBConnectionInformation(
            self.host, self.username, self.password, True)
        self.slave_conn_info = scalr.DBConnectionInformation(
            self.host, self.username, self.password, False)

        self._destroy_test_database()
        warnings.filterwarnings('ignore', category=MySQLdb.Warning)


    def tearDown(self):
        warnings.resetwarnings()
        self._destroy_test_database()

    
    def _direct_cursor(self):
        """
        Bypass our cursor wrapper methods to talk directly to the DB
        """
        connection = MySQLdb.connect(
            host = self.host, user = self.username, passwd = self.password)

        return connection.cursor()


    def _destroy_test_database(self):
        cursor = self._direct_cursor()
        try:
            cursor.execute('DROP DATABASE ScalrTest')  # Any changes are removed
            cursor.execute('COMMIT')
        except MySQLdb.OperationalError:  # DB wasn't created
            pass


    def test_create_database(self):
        """
        Check that we create the database and table on the fly
        """
        cursor = self._direct_cursor()

        cursor.execute('SHOW DATABASES')
        self.assertNotIn('ScalrTest', [row[0] for row in cursor.fetchall()])

        self.master_conn_info.insert('val')

        cursor.execute('SHOW DATABASES')
        self.assertIn('ScalrTest', [row[0] for row in cursor.fetchall()])


    def test_ignore_no_database(self):
        """
        Check that we ignore the absence of a database
        """
        self.assertEqual([], self.slave_conn_info.get_values())


    def test_add_values(self):
        """
        Check that we can read the values from the other connection
        """
        values = ['val1', 'val2', 'val3', 'val4']
        for i, value in enumerate(values):
            self.master_conn_info.insert(value)
            self.assertEqual(values[:i+1], self.slave_conn_info.get_values())
