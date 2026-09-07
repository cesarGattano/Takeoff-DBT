{{ config(materialized="table") }}

with source as (
    select * from {{ ref('stg_clients') }}
)

select
    client_id,
    nom,
    prenom,
    nom || ' ' || prenom as nom_complet,
    email,
    date_naissance,
    date_part('year', age(date_naissance))::integer as age,
    ville,
    code_postal,
    pays,
    segment,
    date_inscription,
    actif
from source