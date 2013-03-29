#!/bin/bash

# Install dependencies
apt-get install -y python-mysqldb python-pip
pip --upgrade
pip install jinja2
pip install bottle

# Remove pre-existing install
rm -rf %remote_path%
