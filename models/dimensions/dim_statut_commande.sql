{{ config(materialized="table") }}

with statuts as (
    select distinct statut from {{ ref('stg_commandes') }}
)

select

    row_number() over (order by statut)::integer    as statut_id,
    statut,
    case statut
        when 'Livré'     then 'Commande livrée au client'
        when 'Annulé'    then 'Commande annulée avant expédition'
        when 'Retourné'  then 'Commande retournée après livraison'
        when 'En cours'  then 'Commande en cours de traitement'
        else 'Statut inconnu'
    end as description,
    case statut
        when 'Livré'     then true
        else false
    end as est_final

from statuts