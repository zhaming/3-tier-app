#!/bin/bash

if [ -s /usr/share/scalr/nginx/app-servers.tpl ]; then
  sed -i 's/ip_hash;//g' /usr/share/scalr/nginx/app-servers.tpl
  echo 'Updated Nginx load balancing template'
fi

if [ -s /etc/nginx/app-servers.include ]; then
  sed -i 's/ip_hash;//g' /etc/nginx/app-servers.include
  nginx -s reload
  echo 'Updated Nginx load balancing rules'
fi
