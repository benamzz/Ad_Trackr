#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE metabase;
    CREATE USER metabase WITH ENCRYPTED PASSWORD 'metabase123';
    GRANT ALL PRIVILEGES ON DATABASE metabase TO metabase;
    \c metabase;
    GRANT ALL ON SCHEMA public TO metabase;
EOSQL

echo "✅ Base de données Metabase créée avec succès"
