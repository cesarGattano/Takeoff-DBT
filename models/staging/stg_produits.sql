with source as (
    select * from {{ ref('raw_produits') }}
),

renamed as (
    select
        produit_id::integer,
        nom,
        description,
        categorie,
        sous_categorie,
        marque,
        prix_unitaire::numeric(10,2),
        cout_achat::numeric(10,2),
        stock::integer,
        actif::boolean
    from source
)

select * from renamed