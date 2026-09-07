{{ config(materialized="table") }}

with commandes as (
    select * from {{ ref('stg_commandes') }}
),

lignes as (
    select
        commande_id,
        sum(quantite)       as nb_articles,
        sum(montant_ligne)  as montant_articles
    from {{ ref('stg_lignes_commande') }}
    group by commande_id
),

dim_canal as (
    select * from {{ ref('dim_canal') }}
),

dim_statut as (
    select * from {{ ref('dim_statut_commande') }}
)

select
    c.commande_id,
    c.client_id,
    to_char(c.date_commande, 'YYYYMMDD')::integer   as date_commande_id,
    to_char(c.date_expedition, 'YYYYMMDD')::integer as date_expedition_id,
    to_char(c.date_livraison, 'YYYYMMDD')::integer  as date_livraison_id,
    dc.canal_id,
    ds.statut_id,
    l.nb_articles,
    c.montant_total,
    c.frais_livraison,
    c.montant_remise,
    l.montant_articles,
    case
        when c.date_expedition is not null and c.date_commande is not null
        then (c.date_expedition - c.date_commande)
        else null
    end as delai_expedition_jours,
    case
        when c.date_livraison is not null and c.date_expedition is not null
        then (c.date_livraison - c.date_expedition)
        else null
    end as delai_livraison_jours
from commandes c
left join lignes l         on c.commande_id = l.commande_id
left join dim_canal dc     on c.canal = dc.canal
left join dim_statut ds    on c.statut = ds.statut