#!/usr/bin/python
#coding:utf-8

import os
import MySQLdb
import socket

from bottle import get, post, run, CGIServer, request, redirect
from jinja2 import Template

CONFIG_PATH = '/var/config'
MOUNTPOINT = '/cgi-bin/app.py'
DB = 'test-db'
VALUE_LENGTH = 200
MYSQL_UNKNOWN_DB_CODE = 1049
MYSQL_NO_HOST_CODE = 2005

BASE_TEMPLATE = """
<html>
    <head>
        <title>Scalr Demo App</title>
    </head>
    <body>

    {% block body %}
        <h1>Error</h1>
        <p>Missing Database Connection Info. Run SetMySQLParams.</p>
    {% endblock body %}

    <h1>Server Info</h1>
    <ul>
        <li>hostname: {{ hostname }}</li>
    </ul>

    </body>
</html>
"""

FORM_TEMPLATE = """
{% extends base_template %}
{% block body %}

<h1>New Value (to master)</h1>

<form action="{{ mountpoint }}" method="post">
    <input name="value" type="text"/>
    <input type="submit"/>
</form>

{% block data %}
    <h1>Error</h1>
    <p>No connection to the slave database could be established.</p>
{% endblock data %}

<h1>MySQL Status</h1>
<ul>
    <li>username: {{ connection_info.username }}</li>
    <li>password: {{ connection_info.password }}</li>
    <li>master:  {{ connection_info.master.hostname }} - {{ connection_info.master.ips() }}</li>
    <li>slave:  {{ connection_info.slave.hostname }} - {{ connection_info.slave.ips() }}</li>
    <li>replicating: {{ connection_info.replicating() }}</li>
</ul>

{% endblock body %}
"""

CONNECTED_TEMPLATE = """
{% extends form_template %}

{% block data %}
<h1>Read values (from slave)</h1>
<ol>
    {% for value in values %}
        <li>{{ value }}</li>
    {% else %}
        <li>No data yet - make a request</li>
    {% endfor %}
</ol>
{% endblock data %}
"""

WRITE_ERROR_TEMPLATE = """
{% extends base_template %}
{% block body %}
<h1>Error</h1>
<p>No connection to the master database could be established.</p>
{% endblock body %}
"""

class NoConnectionInfo(Exception):
    """
    Raised when connection info hasn't been made available
    """

class NoConnectionEstablished(Exception):
    """
    Raised when no connection could be established
    """
    def __init__(self, connection_info):
        self.connection_info = connection_info

class DBConnectionInformation(object):
    def __init__(self, hostname, username, password, master):
        self.hostname = hostname
        self.username = username
        self.password = password
        self.master = master

    def ips(self):
        try:
            return ','.join(sorted(socket.gethostbyname_ex(self.hostname)[2]))
        except socket.gaierror as e:
            return 'Resolution error: {0}'.format(e[1])

    def get_cursor(self):
        try:
            connection = MySQLdb.connect(host = self.hostname, user = self.username, passwd = self.password)
        except MySQLdb.OperationalError as e:
            if e[0] == MYSQL_NO_HOST_CODE:
                raise NoConnectionEstablished(self)
            raise

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
            if e[0] == MYSQL_UNKNOWN_DB_CODE:
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
    def inner():
        ctx = {
            'base_template' : Template(BASE_TEMPLATE),
            'form_template' : Template(FORM_TEMPLATE),
            'write_error_template': Template(WRITE_ERROR_TEMPLATE),
            'connected_template' : Template(CONNECTED_TEMPLATE),
            'mountpoint' : MOUNTPOINT,
            'hostname' : socket.gethostname(),
        }
        try:
            ctx['connection_info'] = ConnectionInfo()
        except NoConnectionInfo:
            return ctx['base_template'].render(ctx)
        else:
            try:
                return page(ctx)
            except NoConnectionEstablished as e:
                if e.connection_info.master:
                    template = ctx['write_error_template']
                else:
                    template = ctx['form_template']
                return template.render(ctx)
    return inner


@get('/')
@prepare_page
def page_get(ctx):
    ctx['values'] = ctx['connection_info'].slave.get_values()
    return ctx['connected_template'].render(ctx)


@post('/')
@prepare_page
def page_post(ctx):
    value = request.forms.get('value')
    ctx['connection_info'].master.insert(value)
    return redirect(MOUNTPOINT)


if __name__ == "__main__":
    run(server = CGIServer, debug = True)
