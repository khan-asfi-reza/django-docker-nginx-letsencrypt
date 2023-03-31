#!/bin/bash

set -e

echo "Checking for dhparams.pem"
if [ ! -f "/vol/proxy/ssl-dhparams.pem" ]; then
  echo "dhparams.pem does not exist - creating it"
  openssl dhparam -out /vol/proxy/ssl-dhparams.pem 2048
fi

echo "Checking for fullchain.pem"
if [ ! -f "/etc/letsencrypt/live/${DOMAIN}/fullchain.pem" ]; then
  echo "No SSL cert, enabling HTTP only..."
  envsubst < /nginx_http.conf > /etc/nginx/nginx.conf
else
  echo "SSL cert exists, enabling HTTPS..."
  envsubst < /nginx.conf > /etc/nginx/nginx.conf
fi

nginx-debug -g 'daemon off;'