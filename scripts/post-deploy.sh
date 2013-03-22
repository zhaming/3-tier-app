#!/bin/bash

mkdir -p /usr/lib/cgi-bin
rm -f /usr/lib/cgi-bin/app.py
ln -s /var/www/app/app.py /usr/lib/cgi-bin
