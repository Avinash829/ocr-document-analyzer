#!/bin/sh
set -eu

# Docker creates named-volume roots as root. Initialize only the dedicated
# Paddle cache mount, then permanently drop privileges for the API process.
mkdir -p /home/app/.paddlex
chown app:app /home/app/.paddlex

exec runuser -u app -- "$@"
