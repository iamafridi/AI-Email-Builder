#!/bin/sh
envsubst '${PORT}' < /etc/nginx/conf.d/default.conf > /tmp/default.conf
mv /tmp/default.conf /etc/nginx/conf.d/default.conf
nginx
uvicorn main:app --host 0.0.0.0 --port 8001
