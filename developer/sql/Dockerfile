# syntax=docker/dockerfile:1
FROM mysql

ENV MYSQL_ROOT_PASSWORD=secret
ENV MYSQL_DATABASE=fourthcoffeedb
ENV MYSQL_USER=admindb
ENV MYSQL_PASSWORD=secret

COPY initDatabase.sql /docker-entrypoint-initdb.d/
