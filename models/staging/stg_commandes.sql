with source as (
    select * from {{ ref('raw_commandes') }}
),

renamed as (
    select
        commande_id::integer,
        client_id::integer,
        date_commande::date,
        statut,
        canal,
        montant_total::numeric(10,2),
        frais_livraison::numeric(10,2),
        montant_remise::numeric(10,2),
        date_expedition::date,
        date_livraison::date
    from source
)

select * from renamed