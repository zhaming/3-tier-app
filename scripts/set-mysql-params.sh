#!/bin/bash

mkdir -p /var/config

echo '%writes-endpoint%' > /var/config/mysql-master
echo '%reads-endpoint%' > /var/config/mysql-slave
echo '%username%' > /var/config/mysql-username
echo '%password%' > /var/config/mysql-password

echo 'Successfully updated MySQL params.'
