#!/bin/sh
# Creates the roles and the databases given as arguments. Safe to run again.
# Connection settings come from PGHOST, PGPORT, PGUSER and PGPASSWORD (a superuser).
#
#   sh infra/postgres/setup.sh jumbaq jumbaq_test
set -eu

: "${JUMBAQ_OWNER_PASSWORD:?is not set}"
: "${JUMBAQ_APP_PASSWORD:?is not set}"

for db in "$@"; do
    psql --quiet --dbname=postgres \
        -v db="$db" \
        -v owner_password="$JUMBAQ_OWNER_PASSWORD" \
        -v app_password="$JUMBAQ_APP_PASSWORD" \
        -f "$(dirname "$0")/setup.sql"
    echo "database $db is ready"
done
