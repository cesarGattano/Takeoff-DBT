with source as (
    select * from {{ ref('raw_visites') }}
),

renamed as (
    select
        visite_id::integer,
        client_id::integer,
        date_visite::date,
        canal,
        pages_vues::integer,
        duree_secondes::integer,
        a_converti::boolean,
        device
    from source
)

select * from renamed