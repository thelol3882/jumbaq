-- Creates the roles of jumbaq and one database. Safe to run again.
--   jumbaq_owner  owns the tables and runs the migrations
--   jumbaq_app    the API and the worker; does not own the tables and cannot delete rows

\set ON_ERROR_STOP on

SELECT 'CREATE ROLE jumbaq_owner'
 WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'jumbaq_owner') \gexec
SELECT 'CREATE ROLE jumbaq_app'
 WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'jumbaq_app') \gexec

SELECT format(
    'ALTER ROLE jumbaq_owner LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L',
    :'owner_password') \gexec
SELECT format(
    'ALTER ROLE jumbaq_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE PASSWORD %L',
    :'app_password') \gexec

SELECT format('CREATE DATABASE %I', :'db')
 WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = :'db') \gexec

REVOKE ALL ON DATABASE :"db" FROM PUBLIC;
GRANT CONNECT, TEMPORARY ON DATABASE :"db" TO jumbaq_owner, jumbaq_app;

\connect :"db"

REVOKE ALL ON SCHEMA public FROM PUBLIC;
GRANT USAGE, CREATE ON SCHEMA public TO jumbaq_owner;
GRANT USAGE ON SCHEMA public TO jumbaq_app;

-- Every table the migrations create is readable and writable by the app, never deletable.
ALTER DEFAULT PRIVILEGES FOR ROLE jumbaq_owner IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE ON TABLES TO jumbaq_app;
