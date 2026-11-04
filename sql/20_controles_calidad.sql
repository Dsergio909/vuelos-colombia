-- 20_controles_calidad.sql
-- Informe de calidad de datos: cada control con lo esperado, lo obtenido y si pasa.
-- Las pruebas de tests/ revisan lo mismo; esta tabla es para leerla sin Python.

with c(orden, control, esperado, obtenido) as (
    select 1, 'Filas de Origen-Destino iguales a la API (478.010)',
        478010, (select count(*) from crudo_od)
    union all select 2, 'Filas de Trafico por Equipo iguales a la API (216.599)',
        216599, (select count(*) from crudo_eq)
    union all select 3, 'Años o meses que no se pudieron leer',
        0, (select count(*) from od where fecha_mes is null)
    union all select 4, 'Pasajeros vacios en la fuente (se cuentan como 0)',
        52, (select count(*) from od where pasajeros_vacio)
    union all select 5, 'Valores negativos de pasajeros o carga',
        0, (select count(*) from od where pasajeros < 0 or carga_kg < 0)
    union all select 6, 'Filas fuera del alcance: trafico Especial',
        12240, (select count(*) from od where trafico = 'Especial')
    union all select 7, 'Filas fuera del alcance: internacionales sin Colombia',
        10, (select count(*) from od where trafico <> 'Especial' and not es_colombia)
    union all select 8, 'Paises con tilde sin corregir',
        0, (select count(distinct pais_origen) from od where pais_origen <> strip_accents(pais_origen))
    union all select 9, 'Filas de trafico de Colombia sin ciudad o sin aerolinea',
        0, (select count(*) from v_od where ciudad_o is null or ciudad_d is null or aerolinea is null)
    union all select 10, 'Aeropuertos repetidos (mismo codigo y pais)',
        0, (select count(*) - count(distinct (codigo, pais)) from aeropuertos)
    union all select 11, 'Combinaciones repetidas (aerolinea, mes, ruta, trafico, tipo de vuelo); se dejan',
        73, (select count(*) - count(distinct (sigla, anio, mes, origen, destino, trafico, tipo_vuelo)) from od)
    union all select 12, 'Meses con datos (enero 2020 a junio 2026)',
        78, (select count(distinct fecha_mes) from od)
)
select
    orden,
    control,
    esperado,
    obtenido,
    case when esperado = obtenido then 'Pasa' else 'REVISAR' end as estado
from c
order by orden;
