{{ config(materialized="table") }}

with canaux as (
    select distinct canal from {{ ref('stg_commandes') }}
    union
    select distinct canal from {{ ref('stg_visites') }}
)

select
    row_number() over (order by canal)::integer as canal_id,
    canal,
    case canal
        when 'SEO'    then 'Recherche organique'
        when 'Email'  then 'Campagne email'
        when 'Pub'    then 'Publicité payante'
        when 'Direct' then 'Accès direct'
        else 'Autre'
    end as canal_description,
    case canal
        when 'Pub' then true
        else false
    end as est_payant
from canaux