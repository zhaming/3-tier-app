#!/bin/bash

mkdir -p /var/config

echo '%master-hostname%' > /var/config/mysql-master
echo '%slave-hostname%' > /var/config/mysql-slave
echo '%username%' > /var/config/mysql-username
echo '%password%' > /var/config/mysql-password

echo 'Successfully updates MySQL params.'
