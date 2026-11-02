select
    retour_id,
    delai_retour_jours
from {{ ref('fact_retours') }}
where delai_retour_jours IS NOT NULL AND delai_retour_jours < 0