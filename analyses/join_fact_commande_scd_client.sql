with commandes as (
    select
        commande_id,
        client_id,
        to_date(date_commande_id::text, 'YYYYMMDD') as date_commande,
        montant_total
    from {{ ref('fact_commandes') }}
),

versions as (
    select
        client_id,
        ville,
        code_postal,
        segment,
        case
            when row_number() over (
                partition by client_id order by dbt_valid_from
            ) = 1
            then date '1900-01-01'
            else dbt_valid_from::date
        end as valid_from,
        coalesce(dbt_valid_to::date, date '9999-12-31') as valid_to
    from {{ ref('scd_client_new') }}
)

select
    c.commande_id,
    c.client_id,
    c.date_commande,
    c.montant_total,
    v.ville        as ville_a_la_commande,
    v.code_postal  as code_postal_a_la_commande,
    v.segment      as segment_a_la_commande,
    d.ville        as ville_actuelle,
    d.code_postal  as code_postal_actuel,
    d.segment      as segment_actuel
from commandes c
left join versions v
       on  c.client_id = v.client_id
       and c.date_commande >= v.valid_from
       and c.date_commande <  v.valid_to
left join {{ ref('dim_client') }} d
       on c.client_id = d.client_id
where v.client_id = 2