{{ config(materialized="table") }}

with source as (
    select * from {{ ref('stg_produits') }}
)

select
    produit_id,
    nom,
    description,
    categorie,
    sous_categorie,
    marque,
    prix_unitaire,
    cout_achat,
    (prix_unitaire - cout_achat)::numeric(10,2) as marge_brute,
    round(((prix_unitaire - cout_achat) / prix_unitaire * 100)::numeric, 2) as taux_marge,
    stock,
    actif
from source