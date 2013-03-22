#!/usr/bin/python

import os
import MySQLdb
import socket

from bottle import get, post, run, CGIServer, request, redirect

MOUNTPOINT = '/cgi-bin/app.py'
DB = 'test-db'


def get_credentials(path = "/var/config/"):
    output = {}
    for fname, key in (
            ('mysql-master', 'master'),
            ('mysql-slave', 'slave'),
            ('mysql-username', 'username'),
            ('mysql-password', 'password'),
            ): 
        with open(os.path.join(path, fname)) as f:
            output[key] = f.read().strip()
    return output


FORM = """
<html>
<head>
<title>Scalr Demo</title>
</head>
    <body>
    <h1>New Value (to master)</h1>
    <form action="{0}" method="post">
        <input name="value" type="text"/>
        <input type="submit"/>

        <h1>Read values (from slave)</h1>
    {1}

    <h1>Status</h1>
    {2}
    </body>
</form>
</html>
"""

STATUS_TEMPLATE = """
<ul>
<li>username: {username}</li>
<li>password: {password}</li>
<li>master: {master}</li>
<li>slave: {slave}</li>
<li>replication: {status}</li>
</ul>

"""

def get_status():
    credentials = get_credentials()
    for host in ('master', 'slave'):
        credentials[host] = socket.gethostbyname(credentials[host])
    credentials['status'] = credentials['master'] != credentials['slave']
    return STATUS_TEMPLATE.format(**credentials)


def get_cursor(master = True):
    credentials = get_credentials()
    username = credentials['username']
    password = credentials['password']
    if master:
        host = credentials['master']
    else:
        host = credentials['slave']
    connection = MySQLdb.connect(host = host, user = username, passwd = password)

    cursor = connection.cursor()

    if master:
        cursor.execute('CREATE DATABASE IF NOT EXISTS ScalrTest')
        cursor.execute('USE ScalrTest')
        cursor.execute('CREATE TABLE IF NOT EXISTS ScalrValues (val CHAR(200) CHARACTER SET utf8 COLLATE utf8_bin)')
    else:
        cursor.execute('USE ScalrTest')

    return cursor

VALUES_TEMPLATE = """
<ol>
{0}
</ol>
"""

def get_values():
    try:
        cursor = get_cursor(False)
        cursor.execute('SELECT val FROM ScalrValues')
    except MySQLdb.OperationalError:
        return "Make a request for data to show up."
    else:
        return VALUES_TEMPLATE.format('\n'.join('<li>{0}</li>'.format(value[0]) for value in cursor.fetchall()))

@get('/')
def page_get():   
    return FORM.format(MOUNTPOINT, get_values(), get_status())

@post('/')
def page_post():
    value = request.forms.get('value')
    cursor = get_cursor(True)
    cursor.execute('INSERT INTO ScalrValues (val) VALUES (%s)', value[:200])
    cursor.execute('COMMIT')

    return redirect(MOUNTPOINT)



if __name__ == "__main__":
    run(server = CGIServer)
