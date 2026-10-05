-- Création du rôle reporting
-- Astuce: n'exécute la commande `CREATE ROLE reporting NOLOGIN` que si le rôle n'existe pas déjà.
SELECT 'CREATE ROLE reporting NOLOGIN'
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'reporting') \gexec

-- Création d'un utilisateur reporter avec mot de passe et connexion limitée à 5
-- Astuce: le mot de passe est passé en paramètre via la variable `pwd` (ex: `-v pwd='mon_mot_de_passe'`)
SELECT format(
  'CREATE ROLE %I LOGIN PASSWORD %L IN ROLE reporting
   NOSUPERUSER NOCREATEDB NOCREATEROLE CONNECTION LIMIT 5', :'REPORTING_USER', :'REPORTING_PASSWORD')
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'reporter') \gexec