-- 12_temporadas.sql
-- Pregunta: ¿en que meses se vuela mas?
-- Indice de temporada: pasajeros del mes / promedio mensual de ese año x 100.
-- 100 = un mes normal; 120 = 20 % mas que un mes normal.
-- Se usan 2022 a 2025: 2020 y 2021 estan deformados por la pandemia
-- (de abril a agosto de 2020 casi no hubo vuelos de pasajeros).

with mensual as (
    select anio, mes, trafico, sum(pasajeros) as pasajeros
    from v_od
    where anio between 2022 and 2025
    group by anio, mes, trafico
),
indice as (
    select
        *,
        100.0 * pasajeros / avg(pasajeros) over (partition by anio, trafico) as indice
    from mensual
)
select
    mes,
    trafico,
    round(avg(indice), 1)        as indice_promedio,
    round(min(indice), 1)        as indice_minimo,
    round(max(indice), 1)        as indice_maximo,
    -- puesto del mes dentro del año (1 = el mes con mas pasajeros)
    rank() over (partition by trafico order by avg(indice) desc) as puesto
from indice
group by mes, trafico
order by trafico desc, mes;
