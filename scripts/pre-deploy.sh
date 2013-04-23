#!/bin/bash

# Install dependencies
apt-get install -y python-mysqldb python-pip libapache2-mod-wsgi
pip --upgrade
pip install jinja2
pip install flask

# Remove pre-existing install
rm -rf %remote_path%
