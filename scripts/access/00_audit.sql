-- Audit de la base de données avant opération

-- version de PostgreSQL
SELECT version();
-- rôles existants
\du
-- schémas et leurs droits
\dn+               
-- droits par table
\dp public.*       
-- default privileges existants
\ddp               
-- bases existantes et leurs droits
SELECT datname, datacl FROM pg_database WHERE datname = current_database();