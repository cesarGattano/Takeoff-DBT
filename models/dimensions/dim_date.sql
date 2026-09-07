{{ config(materialized="table") }}

with dates as (
    select generate_series(
        '2023-01-01'::date,
        '2024-12-31'::date,
        '1 day'::interval
    )::date as date_jour
)

select
    to_char(date_jour, 'YYYYMMDD')::integer     as date_id,
    date_jour,
    date_part('day', date_jour)::integer         as jour,
    date_part('month', date_jour)::integer       as mois,
    to_char(date_jour, 'TMMonth')                as mois_nom,
    date_part('quarter', date_jour)::integer     as trimestre,
    date_part('year', date_jour)::integer        as annee,
    date_part('isodow', date_jour)::integer      as jour_semaine,
    to_char(date_jour, 'TMDay')                  as jour_semaine_nom,
    case
        when date_part('isodow', date_jour) in (6, 7) then true
        else false
    end                                          as est_weekend
from dates