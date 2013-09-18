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
    # Remove debian default configuration
    a2enmod wsgi
    a2dissite 000-default
    # Reload Apache
    service apache2 reload
fi

if [ "$OS" = "redhat" ]; then
    # Create an empty directory for Apache's DocumentRoot
    mkdir /var/www/html

    # Reload Apache
    service httpd restart
fi
