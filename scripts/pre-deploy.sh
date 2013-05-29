#!/bin/bash

# Install dependencies
apt-get install -y python-mysqldb python-flask libapache2-mod-wsgi

# Remove pre-existing install
rm -rf %remote_path%
