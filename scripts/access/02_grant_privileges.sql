-- Grant privileges to group reporting
-- Connect to the database
GRANT CONNECT ON DATABASE datawarehouse_e6 TO reporting;
-- Access to the object within the public schema
GRANT USAGE ON SCHEMA public TO reporting;
-- SELECT privileges on curated tables and views (except dim_client)
GRANT SELECT ON
  public.dim_canal, public.dim_date, public.dim_produit,
  public.dim_statut_commande,
  public.fact_commandes, public.fact_visites, public.fact_retours
TO reporting;
-- SELECT privileges on dim_client [RGPD]: non-identifying columns
GRANT SELECT (client_id, ville, code_postal, pays, segment,
              date_inscription, actif)
ON public.dim_client TO reporting;