-- 15_carga.sql
-- Pregunta: ¿por donde sale y entra la carga aerea, y en que meses?
-- carga_kg incluye el correo (asi lo reporta Aerocivil).
-- Se separa la carga que SALE de Colombia (exportaciones) de la que ENTRA.
-- Meses de 2022 a 2025, con su indice de temporada (100 = mes normal).

with mensual as (
    select
        anio,
        mes,
        case
            when trafico = 'Nacional' then 'Nacional'
            when pais_origen = 'COLOMBIA' then 'Sale de Colombia'
            else 'Entra a Colombia'
        end as sentido,
        sum(carga_kg) / 1000 as toneladas
    from v_od
    where anio between 2022 and 2025
    group by all
),
indice as (
    select *, 100.0 * toneladas / avg(toneladas) over (partition by anio, sentido) as indice
    from mensual
)
select
    sentido,
    mes,
    round(avg(toneladas), 0) as toneladas_promedio_mes,
    round(avg(indice), 1)    as indice_promedio,
    rank() over (partition by sentido order by avg(indice) desc) as puesto
from indice
group by sentido, mes
order by sentido, mes;
