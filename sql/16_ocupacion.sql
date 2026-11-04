-- 16_ocupacion.sql
-- Pregunta: ¿que tan llenos van los aviones? (factor de ocupacion)
-- Sale del conjunto Trafico por Equipo, que trae sillas ofrecidas por vuelo.
-- Ocupacion = pasajeros a bordo / sillas ofrecidas.
-- Solo vuelos regulares con sillas reportadas (los taxis aereos reportan 0 sillas).

select
    anio,
    trafico,
    sum(vuelos)                       as vuelos,
    sum(sillas)                       as sillas,
    sum(pasajeros_a_bordo)            as pasajeros_a_bordo,
    round(100.0 * sum(pasajeros_a_bordo) / sum(sillas), 1) as ocupacion_pct,
    round(sum(pasajeros_a_bordo) / sum(vuelos), 0)         as pasajeros_por_vuelo
from eq
where es_colombia
  and tipo_vuelo = 'Regular'
  and sillas > 0
group by anio, trafico
order by trafico desc, anio;
