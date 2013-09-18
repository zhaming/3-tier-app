#!/bin/bash
# Crash eagerly
set -o errexit
set -o nounset

PID_FILE=/var/run/webapp.pid

# Kill existing process, if it exists
kill `cat $PID_FILE` || true

# Launch our process
gunicorn --chdir %remote_path%/app --daemon --pid $PID_FILE --bind 0.0.0.0:8000 \
  --access-logfile /var/log/webapp.access.log --error-logfile /var/log/webapp.error.log \
  web:application
