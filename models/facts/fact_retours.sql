{{ config(materialized="table") }}


with retours as (
    select * from {{ ref('stg_retours') }}
),

dim_client as (
    select * from {{ ref('dim_client') }}
),

dim_produit as (
    select * from {{ ref('dim_produit') }}
),

lignes as (
    select
        commande_id,
        produit_id,
        montant_ligne
    from {{ ref('stg_lignes_commande') }}
),

commande as (
    select
        commande_id,
        date_commande,
        date_expedition,
        date_livraison
    from {{ ref('stg_commandes')}}
)

select
    r.retour_id,
    r.commande_id,
    to_char(c.date_commande, 'YYYYMMDD')::integer   as date_commande_id,
    to_char(c.date_expedition, 'YYYYMMDD')::integer as date_expedition_id,
    to_char(c.date_livraison, 'YYYYMMDD')::integer   as date_livraison_id,
    to_char(r.date_retour, 'YYYYMMDD')::integer   as date_retour_id,
    dc.client_id,
    dp.produit_id,
    r.motif,
    l.montant_ligne as montant_paye,
    r.montant_rembourse,
    case
        when c.date_livraison is not null
        then (r.date_retour - c.date_livraison)
        when c.date_commande is not null
        then (r.date_retour - c.date_commande)
        else null
    end as delai_retour_jours
from retours r
left join commande c       on r.commande_id = c.commande_id
left join lignes l         on r.commande_id = l.commande_id and r.produit_id = l.produit_id
left join dim_client dc    on r.client_id = dc.client_id
left join dim_produit dp   on r.produit_id = dp.produit_id