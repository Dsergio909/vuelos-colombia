-- 10_resumen_anual.sql
-- Pregunta: ¿cuantos pasajeros y cuanta carga movio Colombia cada año?
-- Solo trafico de Colombia (nacional + internacional). 2026 llega hasta junio.
-- Nota: Aerocivil marca como provisionales las cifras de 2022 a 2025.

select
    anio,
    count(distinct mes)                                              as meses,
    sum(pasajeros)                                                   as pasajeros,
    sum(pasajeros) filter (where trafico = 'Nacional')               as pasajeros_nacionales,
    sum(pasajeros) filter (where trafico = 'Internacional')          as pasajeros_internacionales,
    round(sum(carga_kg) / 1000, 1)                                   as carga_toneladas,
    round(sum(carga_kg) filter (where trafico = 'Internacional') / 1000, 1) as carga_internacional_t,
    -- variacion contra el año anterior (funcion de ventana LAG); solo años completos
    case when count(distinct mes) = 12 and lag(count(distinct mes)) over w = 12 then
        round(100.0 * (sum(pasajeros) - lag(sum(pasajeros)) over w) / lag(sum(pasajeros)) over w, 1)
    end                                                              as variacion_pasajeros_pct
from v_od
group by anio
window w as (order by anio)
order by anio;
