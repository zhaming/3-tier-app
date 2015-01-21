#!/usr/bin/env bash

MYSQL_PASSWORD=APP_TEST_PASSWORD

# Install requirements
sudo apt-get update
sudo apt-get install -q -y python-mysqldb python-flask

# Set test credentials for MySQL
echo mysql-server-5.5 mysql-server/root_password password $MYSQL_PASSWORD | debconf-set-selections
echo mysql-server-5.5 mysql-server/root_password_again password $MYSQL_PASSWORD | debconf-set-selections

# Install test dependencies
sudo apt-get install -q -y mysql-server-5.5 mysql-client-5.5
sudo apt-get install -q -y python-nose python-mock python-coverage

# Install Lighttpd for reports, and make /var/www writable by vagrant user
sudo apt-get install -q -y lighttpd
sudo chown www-data:www-data /var/www
sudo chmod g+rwx /var/www
sudo usermod -aG www-data vagrant

# Set default nose options
cat > /home/vagrant/.noserc << EOF
[nosetests]
verbosity=2
where=/vagrant
with-coverage=1
cover-package=scalr
cover-erase=1
cover-html=1
cover-html-dir=/var/www
EOF

cat > /home/vagrant/.coveragerc << EOF
[run]
branch=True
EOF

# Enable the app to run from localhost
mkdir -p /var/config
echo localhost > /var/config/mysql-master
echo localhost > /var/config/mysql-slave
echo root > /var/config/mysql-username
echo $MYSQL_PASSWORD > /var/config/mysql-password
