FROM postgres:16

# Run create.sql on init
ADD db/create_db.sql /docker-entrypoint-initdb.d
