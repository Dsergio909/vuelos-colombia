-- 11_rutas_principales.sql
-- Pregunta: ¿que rutas mueven mas pasajeros?
-- Una ruta no tiene direccion: Bogota-Medellin suma los dos sentidos.
-- Se compara 2025 (ultimo año completo) con 2024.

with por_ruta as (
    select
        ruta,
        trafico,
        sum(pasajeros) filter (where anio = 2024) as pasajeros_2024,
        sum(pasajeros) filter (where anio = 2025) as pasajeros_2025,
        round(sum(carga_kg) filter (where anio = 2025) / 1000, 1) as carga_2025_t
    from v_od
    group by ruta, trafico
),
con_rango as (
    select
        p.*,
        r.ciudad_a,
        r.ciudad_b,
        -- puesto dentro de su tipo de trafico (nacional o internacional)
        rank() over (partition by p.trafico order by p.pasajeros_2025 desc nulls last) as puesto,
        round(100.0 * p.pasajeros_2025 / sum(p.pasajeros_2025) over (partition by p.trafico), 2)
            as participacion_pct,
        round(100.0 * (p.pasajeros_2025 - p.pasajeros_2024) / nullif(p.pasajeros_2024, 0), 1)
            as variacion_pct
    from por_ruta p
    join rutas r using (ruta, trafico)
)
select
    trafico, puesto, ruta, ciudad_a, ciudad_b,
    pasajeros_2024, pasajeros_2025, variacion_pct, participacion_pct, carga_2025_t,
    -- cuanto suman las rutas hasta este puesto (concentracion acumulada)
    round(sum(participacion_pct) over (partition by trafico order by puesto), 2) as participacion_acumulada_pct
from con_rango
where puesto <= 15
order by trafico desc, puesto;
