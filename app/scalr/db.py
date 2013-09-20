#coding:utf-8
import socket
import random

import MySQLdb

from scalr import exceptions

VALUE_LENGTH = 200
DEFAULT_DB = "ScalrTest"

MYSQL_ERROR_CODE_UNKNOWN_DB = 1049
MYSQL_ERROR_UNKNOWN_TABLE = 1146
MYSQL_ERROR_CODE_NO_HOST = 2005
MYSQL_ERROR_CODE_ACCESS_DENIED = 1045

MYSQL_ERROR_MSG = "A MySQL error occurred: The MySQL Error Code was [{0}]"


class ConnectionInfo(object):
    """
    The DB Connection configuration. We keep the hostnames for the master and
    the slaves, as well as the connection credentials.

    Optionally we can store the database to use.
    """

    def __init__(self, username, password, _master, _slave,
                 database=DEFAULT_DB):
        self.username = username
        self.password = password
        self._master = _master
        self._slave = _slave
        self.database = database

    def _connection(self, master):
        """
        Get a DB connection to the master or the slaves, depending on the
        `master` variable.
        """
        return DBConnection(self.master_ip if master else self.slave_ip,
                            self.username, self.password, master,
                            self.database)

    @property
    def master_ip(self):
        return self._master

    @property
    def slave_ips(self):
        if not self._slave:
            return [self._master]
        return self._slave.split()

    @property
    def slave_ip(self):
        return random.choice(self.slave_ips)

    @property
    def master(self):
        """
        DB Connection to the master
        """
        return self._connection(True)

    @property
    def slave(self):
        """
        DB Connection to the slaves
        """
        return self._connection(False)

    def replicating(self):
        """
        Indicate whether the Master Hostname and Slave Hostname resolve to
        something different - in which case we assume we're replicating.
        """
        return bool(self._slave)


class DBConnection(object):
    """
    A "Connection" to the Database. We can use this to get a cursor, add
    values or list values that are in the Database.
    """
    def __init__(self, hostname, username, password, master,
                 database=DEFAULT_DB):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.master = master
        self.database = database

    def get_cursor(self):
        """
        Get a cursor and do initialization logic (if required), depending on
        whether we are a Master or a Slave.
        """

        try:
            connection = MySQLdb.connect(host=self.hostname,
                                         user=self.username,
                                         passwd=self.password,
                                         charset='utf8')

        except MySQLdb.MySQLError as err:
            error_code = err[0]

            if error_code == MYSQL_ERROR_CODE_NO_HOST:
                msg = u'The host [{0}] does not exist.'.format(self.hostname)
                raise exceptions.NoHost(self, msg)

            if error_code == MYSQL_ERROR_CODE_ACCESS_DENIED:
                msg = u'The username [{0}] or password [{1}] is incorrect.'\
                      .format(self.username, 'redacted')
                raise exceptions.InvalidCredentials(self, msg)

            msg = MYSQL_ERROR_MSG.format(error_code)
            raise exceptions.NoConnectionEstablished(self, msg)

        cursor = connection.cursor()

        # Escaping doesn't work for db statements, but the user doesn't
        # control self.database
        if self.master:
            cursor.execute('CREATE DATABASE IF NOT EXISTS %s' % self.database)
            cursor.execute('USE %s' % self.database)
            cursor.execute('CREATE TABLE IF NOT EXISTS ScalrValues ('
                           'id MEDIUMINT NOT NULL AUTO_INCREMENT,' 
                           'val CHAR (%s) CHARACTER SET utf8 COLLATE utf8_bin,'
                           'PRIMARY KEY (id)'
                           ')',
                           VALUE_LENGTH)

        else:
            cursor.execute('USE %s' % self.database)

        return cursor

    def get_values(self):
        """
        Retrieve all the values we added to the table.
        Fail passively and return an empty list if there is no database or
        table.
        """

        try:
            cursor = self.get_cursor()
            cursor.execute('SELECT val FROM ScalrValues ORDER BY id DESC')

        except MySQLdb.MySQLError as err:
            error_code = err[0]
            if error_code in (MYSQL_ERROR_CODE_UNKNOWN_DB,
                              MYSQL_ERROR_UNKNOWN_TABLE):
                return []  # We lazily create the DB and table here.
            msg = MYSQL_ERROR_MSG.format(error_code)
            raise exceptions.NoConnectionEstablished(self, msg)

        else:
            return [value[0].decode('utf-8') for value in cursor.fetchall()]

    def insert(self, value):
        """
        Insert a new value to the table.
        """

        cursor = self.get_cursor()
        cursor.execute('INSERT INTO ScalrValues (val) VALUES (%s)',
                       value[:VALUE_LENGTH].encode('utf-8'))
        cursor.execute('COMMIT')
