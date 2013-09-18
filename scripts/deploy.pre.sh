#!/bin/bash

# Crash eagerly
set -e

# Identify the OS
if [ -f /etc/debian_version ]; then
    OS=debian
elif [ -f /etc/redhat-release ]; then
    OS=redhat
else
    echo "Unsupported OS"
    exit 1
fi

echo "Identified OS: $OS"

if [ "$OS" = "debian" ]; then
    apt-get install -y python-mysqldb python-flask libapache2-mod-wsgi

    service apache2 restart
fi

if [ "$OS" = "redhat" ]; then
    yum -y install MySQL-python mod_wsgi

    easy_install pip
    pip install flask  # Outdated flask in the packages

    # Configure mod_wsgi to use a writabe location
    echo "WSGISocketPrefix /var/run/wsgi" > /etc/httpd/conf.d/webapp.conf

    service httpd restart
fi

# Remove pre-existing install
rm -rf %remote_path%
