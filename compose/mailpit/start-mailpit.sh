#!/bin/sh

set -e

exec /mailpit \
    --smtp-auth-accept-any="${MAILPIT_SMTP_AUTH_ACCEPT_ANY}" \
    --smtp-auth-allow-insecure="${MAILPIT_SMTP_AUTH_ALLOW_INSECURE}" \
    --max="${MAILPIT_MAX_MESSAGES}" \
    --listen="${MAILPIT_UI_BIND_ADDR}" \
    --smtp="${MAILPIT_SMTP_BIND_ADDR}" \
    --webroot="${MAILPIT_WEBROOT}"
