#!/bin/bash
# Crash eagerly
set -o errexit
set -o nounset


# Set default configuration parameters

DEFAULT_DEPLOY_PATH=/opt/scalr/webapp
DEFAULT_APP_REPO=https://github.com/scalr-tutorials/3-tier-app.git
DEFAULT_APP_BRANCH=master
DEFAULT_PID_FILE=/var/run/webapp.pid
DEFAULT_PORT=8000


# Use configuration from the environment if provided
# Fall back to defaults if no configuration is provided
# Note: environment variables can be provided using Scalr Global Variables

: ${DEPLOY_PATH:="$DEFAULT_DEPLOY_PATH"}
: ${APP_REPO:="$DEFAULT_APP_REPO"}
: ${APP_BRANCH:="$DEFAULT_APP_BRANCH"}
: ${PID_FILE:="$DEFAULT_PID_FILE"}
: ${PORT:="$DEFAULT_PORT"}


# Install system dependencies
# Check operating system first

if [ -f /etc/debian_version ]; then
  OS=debian
  apt-get update
  apt-get install -y git python-mysqldb python-setuptools
elif [ -f /etc/redhat-release ]; then
  OS=redhat
  yum -y install git MySQL-python
else
    echo "Unsupported OS"
    exit 1
fi


# Instal python dependencies
# This is platform-independent

easy_install pip
pip install flask gunicorn


# If the app hasn't been deployed yet, create the path, and deploy the app
# If the app had been deployed before, update it

if [ ! -d "$DEPLOY_PATH" ]; then
  mkdir -p $DEPLOY_PATH
  rm -r $DEPLOY_PATH
  git clone --branch $APP_BRANCH $APP_REPO $DEPLOY_PATH
else
  cd $DEPLOY_PATH
  git pull
  git checkout $APP_BRANCH
fi


# If any existing app processes are alive, kill them

kill `cat $PID_FILE 2>/dev/null` || true


# Launch the app
gunicorn --chdir $DEPLOY_PATH/app --daemon --pid $PID_FILE --bind 0.0.0.0:$PORT \
  --access-logfile /var/log/webapp.access.log --error-logfile /var/log/webapp.error.log \
  web:application


echo "Started Webapp - listening on $PORT"
