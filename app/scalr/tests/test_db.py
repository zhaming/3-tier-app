#coding:utf-8
import MySQLdb
import unittest
import warnings

from scalr import exceptions
from scalr import db

from scalr.tests import TEST_DB_CONFIG


class DBTestCase(unittest.TestCase):
    def setUp(self):
        self.conn_info = db.ConnectionInfo(**TEST_DB_CONFIG)


class DBConnectionFailureTestCase(DBTestCase):
    def test_no_host(self):
        """
        Check that we handle invalid host setup
        """
        self.conn_info._master = "invalid"
        conn = self.conn_info.master
        self.assertRaises(exceptions.NoHost, conn.get_cursor)

    def test_invalid_credentials(self):
        """
        Check that we handle invalid username
        """
        self.conn_info.username = "invalid"
        conn = self.conn_info.master
        self.assertRaises(exceptions.InvalidCredentials, conn.get_cursor)

    def test_invalid_password(self):
        """
        Check that we handle an invalid password
        """
        self.conn_info.password = "invalid"
        conn = self.conn_info.master
        self.assertRaises(exceptions.InvalidCredentials, conn.get_cursor)


class DBInstructionsTestCase(DBTestCase):
    def setUp(self):
        super(DBInstructionsTestCase, self).setUp()

        self.master_conn = self.conn_info.master
        self.slave_conn = self.conn_info.slave

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
            host=self.conn_info._master, user=self.conn_info.username,
            passwd=self.conn_info.password)

        return connection.cursor()

    def _destroy_test_database(self):
        cursor = self._direct_cursor()
        try:
            # Any changes are removed
            cursor.execute('DROP DATABASE %s' % self.conn_info.database)
            cursor.execute('COMMIT')
        except MySQLdb.OperationalError:  # DB wasn't created
            pass

    def test_create_database(self):
        """
        Check that we create the database and table on the fly
        """
        cursor = self._direct_cursor()

        cursor.execute('SHOW DATABASES')
        self.assertNotIn(self.conn_info.database,
                         [row[0] for row in cursor.fetchall()])

        self.master_conn.insert('val')

        cursor.execute('SHOW DATABASES')
        self.assertIn(self.conn_info.database,
                      [row[0] for row in cursor.fetchall()])

    def test_ignore_no_database(self):
        """
        Check that we ignore the absence of a database
        """
        self.assertEqual([], self.slave_conn.get_values())

    def test_add_values(self):
        """
        Check that we can read the values from the other connection
        """
        values = ['val1', 'val2', 'val3', 'val4']
        for i, value in enumerate(values):
            self.master_conn.insert(value)
            expected = (values[:i+1])
            expected.reverse()
            self.assertEqual(expected, self.slave_conn.get_values())
