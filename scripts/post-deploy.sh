#!/bin/bash

# Enable Apache mod_wsgi and remove the default site
a2enmod wsgi
a2dissite 000-default

service apache2 reload
