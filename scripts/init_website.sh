#!/bin/bash
mkdir -p /var/www/html
cp -r /app/skillhub/* /var/www/html 2>/dev/null || true
