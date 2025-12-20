\set authenticator_password `echo "$POSTGRES_AUTHENTICATOR_PASSWORD"`
\set pgbouncer_password `echo "$POSTGRES_PGBOUNCER_PASSWORD"`
\set auth_admin_password `echo "$POSTGRES_SUPABASE_AUTH_ADMIN_PASSWORD"`
\set functions_admin_password `echo "$POSTGRES_SUPABASE_FUNCTIONS_ADMIN_PASSWORD"`
\set storage_admin_password `echo "$POSTGRES_SUPABASE_STORAGE_ADMIN_PASSWORD"`


ALTER USER authenticator WITH PASSWORD :'authenticator_password';
ALTER USER pgbouncer WITH PASSWORD :'pgbouncer_password';
ALTER USER supabase_auth_admin WITH PASSWORD :'auth_admin_password';
ALTER USER supabase_functions_admin WITH PASSWORD :'functions_admin_password';
ALTER USER supabase_storage_admin WITH PASSWORD :'storage_admin_password';
