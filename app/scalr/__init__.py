#coding:utf-8

import socket
import functools

from flask import Flask, request, redirect, url_for, flash, render_template

from scalr import exceptions
from scalr import config

app = Flask(__name__)
app.secret_key = 'no_sensitive_data_here'
CONFIG_PATH = '/var/config'


def prepare_page(takes_context = False):
    def wrap(page):
        @functools.wraps(page)
        def inner():
            ctx = {
                'mountpoint' : url_for('page_post'),
                'hostname' : socket.gethostname(),
            }

            # Do we have connection data?
            try:
                connection_info = config.parse_config(CONFIG_PATH)
            except exceptions.NoConnectionInfo:
                flash('Missing connection info!', 'error')
                return render_template('base.html', **ctx)

            # Does it work?
            try:
                output = page(connection_info, **(ctx if takes_context else {}))
            except exceptions.NoConnectionEstablished as err:
                ctx['error'] = err.error
                if err.connection_info.master:
                    flash('Could not write to the master database!', 'error')
                    template = 'write_error.html'
                else:
                    flash('Could not connect to the slave database!', 'error')
                    template = 'read_error.html'
                return render_template(template,
                    connection_info = connection_info, **ctx)

            return output

        return inner
    return wrap


@app.route('/', methods = ['GET', 'HEAD'])
@prepare_page(takes_context = True)
def page_get(connection_info, **ctx):
    values = connection_info.slave.get_values()
    return render_template('connected.html',
            connection_info=connection_info, values=values, **ctx)


@app.route('/', methods = ['POST'])
@prepare_page()
def page_post(connection_info):
    value = request.form.get('value')
    connection_info.master.insert(value)
    flash('Your value ({0}) was written to the database!'.format(value), 'success')
    return redirect(url_for('page_get'))
