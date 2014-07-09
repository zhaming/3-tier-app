#coding:utf-8

import socket
import functools
import logging

from flask import Flask, request, redirect, url_for, flash, render_template

from scalr import exceptions
from scalr import config

app = Flask(__name__)
app.secret_key = 'no_sensitive_data_here'
app_handler = logging.FileHandler('/tmp/app.log')
app_handler.setLevel(logging.DEBUG)
app_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(app_handler)

CONFIG_PATH = '/var/config'


def prepare_page(takes_context=False):
    """
    Decorate the pages with common exception handling / error reporting
    """

    def wrap(page):
        @functools.wraps(page)
        def inner():
            ctx = {
                'mountpoint': url_for('page_post'),
                'hostname': socket.gethostname(),
            }

            # Do we have connection data?
            try:
                connection_info = config.parse_config(CONFIG_PATH)
            except exceptions.NoConnectionInfo:
                flash(u'MySQL connection information is unavailable', 'error')
                return render_template('config_error.html', **ctx)

            # Does it work?
            try:
                output = page(connection_info,
                              **(ctx if takes_context else {}))
            except exceptions.NoConnectionEstablished as err:
                ctx['error'] = err.error
                if err.connection_info.master:
                    flash(u'An error occurred when writing '
                          u'to the Master MySQL database!', 'error')
                    template = 'write_error.html'
                else:
                    flash(u'An error occurred when reading '
                          u'from a Slave MySQL database!', 'error')
                    template = 'read_error.html'
                return render_template(template,
                                       connection_info=connection_info,
                                       **ctx)

            return output

        return inner
    return wrap


@app.route('/', methods=['GET', 'HEAD'])
@prepare_page(takes_context=True)
def page_get(connection_info, **ctx):
    """
    Display the values form (if we had no errors so far)
    """

    values = connection_info.slave.get_values()
    return render_template('connected.html',
                           connection_info=connection_info, values=values,
                           **ctx)


@app.route('/', methods=['POST'])
@prepare_page()
def page_post(connection_info):
    """
    Add the `value` form parameter to the database and return to the homepage.
    """

    value = request.form.get('value')
    connection_info.master.insert(value)
    flash(u'Your message ({0}) was written to the database!'.format(value),
          'success')
    return redirect(url_for('page_get'))
