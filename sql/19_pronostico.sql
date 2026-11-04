-- 19_pronostico.sql
-- Pregunta: ¿cuantos pasajeros se pueden esperar de julio a diciembre?
-- Metodo (simple a proposito, para poder explicarlo):
--   1. Indice de temporada de cada mes con los 3 años completos anteriores.
--   2. Con lo real de enero a junio se calcula el "nivel" del año:
--        nivel = pasajeros reales ene-jun / suma de los indices de ene-jun
--   3. Pronostico de cada mes de julio a diciembre = nivel x indice del mes.
-- Primero se prueba con 2025 (se pronostica jul-dic de 2025 como si no se
-- supiera y se compara con lo real). Despues se aplica a 2026.

create or replace table pronostico as
with mensual as (
    select anio, mes, trafico, sum(pasajeros) as pasajeros
    from v_od
    group by all
),
indice as (
    select *, pasajeros / avg(pasajeros) over (partition by anio, trafico) as idx
    from mensual
    where anio between 2022 and 2025
),
casos(objetivo, desde, hasta, tipo) as (
    values (2025, 2022, 2024, 'Prueba con 2025'),
           (2026, 2023, 2025, 'Pronostico 2026')
),
indice_caso as (
    select c.objetivo, c.tipo, i.mes, i.trafico, avg(i.idx) as idx
    from casos c
    join indice i on i.anio between c.desde and c.hasta
    group by all
),
nivel as (
    select ic.objetivo, ic.trafico,
           sum(m.pasajeros) / sum(ic.idx) as nivel
    from indice_caso ic
    join mensual m on m.anio = ic.objetivo and m.mes = ic.mes and m.trafico = ic.trafico
    where ic.mes <= 6
    group by all
)
select
    ic.tipo,
    ic.objetivo as anio,
    ic.mes,
    ic.trafico,
    round(n.nivel * ic.idx)                                             as pronostico,
    m.pasajeros                                                         as real,
    round(100.0 * (n.nivel * ic.idx - m.pasajeros) / m.pasajeros, 1)    as error_pct
from indice_caso ic
join nivel n using (objetivo, trafico)
left join mensual m on m.anio = ic.objetivo and m.mes = ic.mes and m.trafico = ic.trafico
where ic.mes >= 7;

select * from pronostico
order by anio, trafico desc, mes;
