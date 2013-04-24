#coding:utf-8
import socket
import MySQLdb

from scalr import exceptions

VALUE_LENGTH = 200
DEFAULT_DB = "ScalrTest"

MYSQL_ERROR_CODE_UNKNOWN_DB = 1049
MYSQL_ERROR_UNKNOWN_TABLE = 1146
MYSQL_ERROR_CODE_NO_HOST = 2005
MYSQL_ERROR_CODE_ACCESS_DENIED = 1045


class ConnectionInfo(object):

    def __init__(self, username, password, _master, _slave):
        self.username = username
        self.password = password
        self._master = _master
        self._slave = _slave

    def _connection_information(self, master):
        return DBConnection(self._master if master else self._slave,
                                       self.username, self.password, master)

    @property
    def master(self):
        return self._connection_information(True)

    @property
    def slave(self):
        return self._connection_information(False)

    def replicating(self):
        return self.master.ips() != self.slave.ips()


class DBConnection(object):
    def __init__(self, hostname, username, password, master, database = DEFAULT_DB):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.master = master
        self.database = database

    def ips(self):
        try:
            return sorted(socket.gethostbyname_ex(self.hostname)[2])
        except socket.gaierror as e:
            return ('Resolution error: {0}'.format(e[1]),)  # (Rendering)

    def get_cursor(self):
        try:
            connection = MySQLdb.connect(host = self.hostname, user = self.username, passwd = self.password)
        except MySQLdb.MySQLError as e:
            error_code = e[0]
            if error_code == MYSQL_ERROR_CODE_NO_HOST:
                raise exceptions.NoHost(self, "The host [{0}] does not exist.".format(self.hostname))
            if error_code == MYSQL_ERROR_CODE_ACCESS_DENIED:
                raise exceptions.InvalidCredentials(self, "The username [{0}] or password [{1}] is incorrect.".format(self.username, 'redacted'))
            raise exceptions.NoConnectionEstablished(self, "An error occured: Code {0}".format(error_code))

        cursor = connection.cursor()

        # Escaping doesn't work for db statements, but the user doesn't
        # control self.database
        if self.master:
            cursor.execute('CREATE DATABASE IF NOT EXISTS %s' % self.database)
            cursor.execute('USE %s' % self.database)
            cursor.execute('CREATE TABLE IF NOT EXISTS ScalrValues (val CHAR(%s) CHARACTER SET utf8 COLLATE utf8_bin)', VALUE_LENGTH)
        else:
            cursor.execute('USE %s' % self.database)

        return cursor

    def get_values(self):
        try:
            cursor = self.get_cursor()
            cursor.execute('SELECT val FROM ScalrValues')
        except MySQLdb.MySQLError as e:
            error_code = e[0]
            if error_code in (MYSQL_ERROR_CODE_UNKNOWN_DB, MYSQL_ERROR_UNKNOWN_TABLE):
                return [] # We lazily create the DB and table here.
            raise exceptions.NoConnectionEstablished(self, "An error occured: Code {0}".format(error_code))
        else:
            return [value[0] for value in cursor.fetchall()]

    def insert(self, value):
        cursor = self.get_cursor()
        cursor.execute('INSERT INTO ScalrValues (val) VALUES (%s)', value[:VALUE_LENGTH])
        cursor.execute('COMMIT')
