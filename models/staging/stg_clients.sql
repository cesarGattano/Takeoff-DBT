with source as (
    select * from {{ ref('raw_clients') }}
),

renamed as (
    select
        client_id::integer,
        nom,
        prenom,
        email,
        date_naissance::date,
        ville,
        code_postal,
        pays,
        segment,
        date_inscription::date,
        actif::boolean
    from source
)

select * from renamed