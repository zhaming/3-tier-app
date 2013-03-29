#!/bin/bash

# Remove a pre-existing install
mkdir -p /usr/lib/cgi-bin
rm -f /usr/lib/cgi-bin/app.py

# Symlink the app to cgi-bin
cd %remote_path%
ln -s app/app.py /usr/lib/cgi-bin
