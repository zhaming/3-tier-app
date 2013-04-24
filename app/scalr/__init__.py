#coding:utf-8

import os
import MySQLdb
import socket
import functools

from flask import Flask, request, redirect, url_for
from jinja2 import Environment, PackageLoader

app = Flask(__name__)
env = Environment(loader=PackageLoader('scalr'))

CONFIG_PATH = '/var/config'
DB = 'test-db'
VALUE_LENGTH = 200

MYSQL_ERROR_CODE_UNKNOWN_DB = 1049
MYSQL_ERROR_CODE_NO_HOST = 2005
MYSQL_ERROR_CODE_ACCESS_DENIED = 1045


class NoConnectionInfo(Exception):
    """
    Raised when connection info hasn't been made available
    """


class NoConnectionEstablished(Exception):
    """
    Raised when no connection could be established
    """
    def __init__(self, connection_info, error):
        self.connection_info = connection_info
        self.error = error


class DBConnectionInformation(object):
    def __init__(self, hostname, username, password, master):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.master = master

    def ips(self):
        try:
            return sorted(socket.gethostbyname_ex(self.hostname)[2])
        except socket.gaierror as e:
            return ('Resolution error: {0}'.format(e[1]),)  # (Rendering)

    def get_cursor(self):
        try:
            connection = MySQLdb.connect(host = self.hostname, user = self.username, passwd = self.password)
        except MySQLdb.OperationalError as e:
            error_code = e[0]
            if error_code == MYSQL_ERROR_CODE_NO_HOST:
                raise NoConnectionEstablished(self, "The host [{0}] does not exist.".format(self.hostname))
            if error_code == MYSQL_ERROR_CODE_ACCESS_DENIED:
                raise NoConnectionEstablished(self, "The username [{0}] or password [{1}] is incorrect.".format(self.username, 'redacted'))
            raise NoConnectionEstablished(self, "An error occured: Code {0}".format(error_code))

        cursor = connection.cursor()

        if self.master:
            cursor.execute('CREATE DATABASE IF NOT EXISTS ScalrTest')
            cursor.execute('USE ScalrTest')
            cursor.execute('CREATE TABLE IF NOT EXISTS ScalrValues (val CHAR(%s) CHARACTER SET utf8 COLLATE utf8_bin)', VALUE_LENGTH)
        else:
            cursor.execute('USE ScalrTest')

        return cursor

    def get_values(self):
        try:
            cursor = self.get_cursor()
            cursor.execute('SELECT val FROM ScalrValues')
        except MySQLdb.OperationalError as e:
            if e[0] == MYSQL_ERROR_CODE_UNKNOWN_DB:
                return [] # We lazily create the table here.
            raise
        else:
            return [value[0] for value in cursor.fetchall()]

    def insert(self, value):
        cursor = self.get_cursor()
        cursor.execute('INSERT INTO ScalrValues (val) VALUES (%s)', value[:VALUE_LENGTH])
        cursor.execute('COMMIT')


class ConnectionInfo(object):
    def __init__(self, path = CONFIG_PATH):
        for fname, attr in (
            ('mysql-username', 'username'), ('mysql-password', 'password'),
             ('mysql-master', '_master'), ('mysql-slave', '_slave'),
        ):
            try:
                with open(os.path.join(path, fname)) as f:
                    setattr(self, attr, f.read().strip())
            except IOError:
                raise NoConnectionInfo()

    def _connection_information(self, master):
        return DBConnectionInformation(self._master if master else self._slave,
                                       self.username, self.password, master)

    @property
    def master(self):
        return self._connection_information(True)

    @property
    def slave(self):
        return self._connection_information(False)

    def replicating(self):
        return self.master.ips != self.slave.ips


def prepare_page(page):
    @functools.wraps(page)
    def inner():
        ctx = {
            'mountpoint' : url_for('page_post'),
            'hostname' : socket.gethostname(),
            'error': '',
        }
        try:
            ctx['connection_info'] = ConnectionInfo()
        except NoConnectionInfo:
            return env.get_template('base.html').render(ctx)
        else:
            try:
                return page(ctx)
            except NoConnectionEstablished as err:
                ctx['error'] = err.error
                if err.connection_info.master:
                    template = env.get_template('write_error.html')
                else:
                    template = env.get_template('read_error.html')
                return template.render(ctx)
    return inner


@app.route('/', methods = ['GET', 'HEAD'])
@prepare_page
def page_get(ctx):
    ctx['values'] = ctx['connection_info'].slave.get_values()
    return env.get_template('connected.html').render(ctx)


@app.route('/', methods = ['POST'])
@prepare_page
def page_post(ctx):
    value = request.form.get('value')
    ctx['connection_info'].master.insert(value)
    return redirect(url_for('page_get'))


if __name__ == "__main__":
    app.run(debug = True)
