-- 13_aerolineas.sql
-- Pregunta: ¿que aerolineas mueven a los pasajeros nacionales y como cambio
-- el reparto cuando Viva Air (feb-2023) y Ultra Air (mar-2023) dejaron de volar?
-- Participacion = pasajeros de la aerolinea / pasajeros nacionales del año.
-- HHI (indice de Herfindahl-Hirschman): suma de participaciones al cuadrado.
-- Por encima de 2.500 se considera un mercado muy concentrado.

with por_grupo as (
    select anio, grupo, sum(pasajeros) as pasajeros
    from v_od
    where trafico = 'Nacional'
    group by anio, grupo
),
participacion as (
    select
        *,
        100.0 * pasajeros / sum(pasajeros) over (partition by anio) as participacion_pct
    from por_grupo
)
select
    anio,
    grupo,
    pasajeros,
    round(participacion_pct, 1) as participacion_pct,
    rank() over (partition by anio order by pasajeros desc) as puesto,
    round(sum(participacion_pct * participacion_pct) over (partition by anio)) as hhi_del_anio
from participacion
qualify puesto <= 8
order by anio, puesto;
