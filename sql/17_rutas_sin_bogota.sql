-- 17_rutas_sin_bogota.sql
-- Pregunta: ¿cuanto depende el pais de Bogota y que pasa con las rutas que no pasan por alla?
-- "Punto a punto" = ruta nacional donde ningun extremo es El Dorado (BOG).

with anual as (
    select
        anio,
        case when origen = 'BOG' or destino = 'BOG' then 'Pasa por Bogota' else 'Punto a punto' end as tipo_ruta,
        sum(pasajeros) as pasajeros
    from v_od
    where trafico = 'Nacional'
      and anio between 2020 and 2025
    group by all
)
select
    anio,
    tipo_ruta,
    pasajeros,
    round(100.0 * pasajeros / sum(pasajeros) over (partition by anio), 1) as participacion_pct,
    round(100.0 * (pasajeros - lag(pasajeros) over w) / lag(pasajeros) over w, 1) as variacion_pct
from anual
window w as (partition by tipo_ruta order by anio)
order by anio, tipo_ruta;
