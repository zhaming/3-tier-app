#!/usr/bin/python
#coding:utf-8

import os
import MySQLdb
import socket
import functools

from flask import Flask, request, redirect, url_for
from jinja2 import Template

app = Flask(__name__)

CONFIG_PATH = '/var/config'
DB = 'test-db'
VALUE_LENGTH = 200

MYSQL_ERROR_CODE_UNKNOWN_DB = 1049
MYSQL_ERROR_CODE_NO_HOST = 2005
MYSQL_ERROR_CODE_ACCESS_DENIED = 1045

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>Scalr Demo App</title>
        <link href="//netdna.bootstrapcdn.com/twitter-bootstrap/2.3.1/css/bootstrap-combined.min.css" rel="stylesheet">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body>
        <div class="hero-unit">
         <h1>Welcome to Scalr!</h1>
        </div>
        <div class="container">

            {% block body %}
            <h1>Error</h1>
            <p>Missing Database Connection Info. Run SetMySQLParams.</p>
            {% endblock body %}

            <h1>Server Info</h1>
            <ul>
                <li>Hostname: <code>{{ hostname }}</code></li>
            </ul>

        </div>
    </body>
</html>
"""

FORM_TEMPLATE = """
{% extends base_template %}
{% block body %}

<h1>Write a new Value (to master)</h1>
<p>Use this form to submit values to the database.</p>

<form action="{{ mountpoint }}" method="post" class="form-inline">
    <fieldset>
        <div class="input-append">"
            <input name="value" type="text" placeholder="Some data..."/>
            <input type="submit" class="btn btn-success" value="Write!"/>
        </div>
    </fieldset>
</form>

{% block data %}
{% endblock data %}

<h1>MySQL Status</h1>
<ul>
    <li>Username: <code>{{ connection_info.username }}</code></li>
    <li>Password: <code>[redacted]</code></li>
    <li>
        Master hostname:  <code>{{ connection_info.master.hostname }}</code>
        <ul>
        {% for ip in connection_info.master.ips() %}
            <li><code>{{ ip }}</code></li>
        {% endfor %}
        </ul>
    </li>
    <li>
        Slave hostname:  <code>{{ connection_info.slave.hostname }}</code>
        <ul>
        {% for ip in connection_info.slave.ips() %}
            <li><code>{{ ip }}</code></li>
        {% endfor %}
        </ul>
    </li>
    <li>Replicating: <code>{{ connection_info.replicating() }}</code></li>
</ul>

{% endblock body %}
"""

CONNECTED_TEMPLATE = """
{% extends form_template %}

{% block data %}
<h1>Read Values (from slaves)</h1>
<ul>
    {% for value in values %}
        <li>{{ value }}</li>
    {% else %}
        <li>No data yet - make a request</li>
    {% endfor %}
</ul>
{% endblock data %}
"""

READ_ERROR_TEMPLATE = """
{% extends form_template %}
{% block data %}
<h1>Error</h1>
<p>No connection to the slave database could be established.</p>
<p>The error was: {{ error }}</p>
{% endblock data %}
"""

WRITE_ERROR_TEMPLATE = """
{% extends base_template %}
{% block body %}
<h1>Error</h1>
<p>No connection to the master database could be established.</p>
<p>The error was: {{ error }}</p>
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
            'base_template' : Template(BASE_TEMPLATE),
            'form_template' : Template(FORM_TEMPLATE),
            'read_error_template': Template(READ_ERROR_TEMPLATE),
            'write_error_template': Template(WRITE_ERROR_TEMPLATE),
            'connected_template' : Template(CONNECTED_TEMPLATE),
            'mountpoint' : url_for('page_post'),
            'hostname' : socket.gethostname(),
            'error': '',
        }
        try:
            ctx['connection_info'] = ConnectionInfo()
        except NoConnectionInfo:
            return ctx['base_template'].render(ctx)
        else:
            try:
                return page(ctx)
            except NoConnectionEstablished as err:
                ctx['error'] = err.error
                if err.connection_info.master:
                    template = ctx['write_error_template']
                else:
                    template = ctx['read_error_template']
                return template.render(ctx)
    return inner


@app.route('/', methods = ['GET', 'HEAD'])
@prepare_page
def page_get(ctx):
    ctx['values'] = ctx['connection_info'].slave.get_values()
    return ctx['connected_template'].render(ctx)


@app.route('/', methods = ['POST'])
@prepare_page
def page_post(ctx):
    value = request.form.get('value')
    ctx['connection_info'].master.insert(value)
    return redirect(url_for('page_get'))


if __name__ == "__main__":
    app.run(debug = True)
