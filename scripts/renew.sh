#!/bin/sh
set -e

cd /home/app/

/usr/local/bin/docker-compose -f docker-compose.prod.yaml run --rm certbot certbot renew