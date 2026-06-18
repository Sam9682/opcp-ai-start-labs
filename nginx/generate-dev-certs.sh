#!/bin/bash
# Generate self-signed SSL certificates for development
# These should NOT be used in production

set -e

CERT_DIR="$(dirname "$0")/ssl"
mkdir -p "$CERT_DIR"

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout "$CERT_DIR/key.pem" \
    -out "$CERT_DIR/cert.pem" \
    -subj "/C=FR/ST=IDF/L=Paris/O=OPCP/OU=Training/CN=localhost"

echo "Self-signed certificates generated in $CERT_DIR/"
echo "  - cert.pem (certificate)"
echo "  - key.pem  (private key)"
