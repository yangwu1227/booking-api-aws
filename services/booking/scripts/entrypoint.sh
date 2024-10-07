#!/bin/sh

echo "Waiting for postgres to start..."

while ! nc -z db-test 5432; do
  # The nc (Netcat) is utility to check network connectivity
  # The -z flag ensures nc only scan for open ports without sending data
  # If the connection fails (i.e., PostgreSQL isn't up yet), the loop continues
  sleep 0.1
done

echo "PostgreSQL started"

# 'exec' replaces the current shell process with the command and arguments passed to the script, preserving all arguments as separate arguments
# For example: ./script.sh command --option value -> exec command --option value
exec "$@"
