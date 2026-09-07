with source as (
    select * from {{ ref('raw_lignes_commande') }}
),

renamed as (
    select
        ligne_id::integer,
        commande_id::integer,
        produit_id::integer,
        quantite::integer,
        prix_unitaire::numeric(10,2),
        remise_ligne::numeric(10,2),
        (prix_unitaire * quantite - remise_ligne)::numeric(10,2) as montant_ligne
    from source
)

select * from renamed