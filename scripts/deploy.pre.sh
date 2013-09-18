#!/bin/bash
# Crash eagerly
set -o errexit
set -o nounset


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


# Install System Dependencies

if [ "$OS" = "debian" ]; then
    apt-get install -y python-mysqldb
fi

if [ "$OS" = "redhat" ]; then
    yum -y install MySQL-python
fi


# Instal Python Dependencies

easy_install pip
pip install flask gunicorn

# Remove pre-existing install
rm -rf %remote_path%
