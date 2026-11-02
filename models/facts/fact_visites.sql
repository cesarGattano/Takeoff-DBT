{{ config(materialized="table") }}

with visites as (
    select * from {{ ref('stg_visites') }}
),

dim_canal as (
    select * from {{ ref('dim_canal') }}
)

select
    v.visite_id,
    v.client_id,
    to_char(v.date_visite, 'YYYYMMDD')::integer as date_visite_id,
    dc.canal_id,
    v.pages_vues,
    v.duree_secondes,
    round((v.duree_secondes / 60.0)::numeric, 2) as duree_minutes,
    v.a_converti,
    v.device
from visites v
left join dim_canal dc on v.canal = dc.canal