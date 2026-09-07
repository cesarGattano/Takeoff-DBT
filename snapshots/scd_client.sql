{% snapshot scd_client %}

{{
    config(
        target_schema='public',
        unique_key='client_id',
        strategy='check',
        check_cols=['ville', 'code_postal', 'segment'],
    )
}}

select
    client_id,
    nom,
    prenom,
    email,
    ville,
    code_postal,
    pays,
    segment,
    actif
from {{ ref('stg_clients') }}

{% endsnapshot %}