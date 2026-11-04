-- 14_nacional_internacional.sql
-- Pregunta: ¿cuanto pesa lo internacional y a donde se viaja?
-- Paises fuera de Colombia, por pasajeros de 2025, con su variacion contra 2024.

with por_pais as (
    select
        case when pais_origen = 'COLOMBIA' then pais_destino else pais_origen end as pais,
        sum(pasajeros) filter (where anio = 2024) as pasajeros_2024,
        sum(pasajeros) filter (where anio = 2025) as pasajeros_2025
    from v_od
    where trafico = 'Internacional'
    group by 1
)
select
    rank() over (order by pasajeros_2025 desc nulls last) as puesto,
    pais,
    pasajeros_2024,
    pasajeros_2025,
    round(100.0 * (pasajeros_2025 - pasajeros_2024) / nullif(pasajeros_2024, 0), 1) as variacion_pct,
    round(100.0 * pasajeros_2025 / sum(pasajeros_2025) over (), 1)                  as participacion_pct
from por_pais
qualify puesto <= 12
order by puesto;
