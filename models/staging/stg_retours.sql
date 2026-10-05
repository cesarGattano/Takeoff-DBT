with source as (
    select * from {{ ref('raw_retours') }}
),

renamed as (
    select
        retour_id::integer,
        commande_id::integer,
        produit_id::integer,
        client_id::integer,
        date_retour::date,
        motif,
        montant_rembourse::numeric(10,2)
    from source
)

select * from renamed