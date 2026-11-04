-- 02_limpiar.sql
-- Limpia los datos crudos y arma el modelo que usan las consultas 10 a 18.
--
-- Que se corrige y por que:
--   1. Tipos: año, mes, pasajeros y carga llegan como texto. Se convierten con
--      try_cast; si un valor no se puede leer queda marcado, no se pierde la fila.
--   2. Pasajeros vacios: 52 filas (taxi aereo, casi siempre) no traen pasajeros.
--      Se cuentan como 0 y quedan marcadas en pasajeros_vacio.
--   3. Codigos de una letra: N, I, E y R, T, C, A pasan a palabras.
--   4. Ciudades: el mismo aeropuerto aparece como "CALI" y "SANTIAGO DE CALI",
--      o "MONTERIA" y "MONTERÍA". Se quitan tildes, se toma el nombre mas usado
--      por aeropuerto y se acortan los nombres oficiales largos.
--   5. Aerolineas: una misma sigla OACI trae nombres distintos ("COPA" y
--      "COPA AIRLINES"). Se usa el nombre del ultimo mes reportado.
--   6. Paises: llegan con y sin tilde ("PANAMA" y "PANAMÁ", "ESPAÑA" y "ESPANA").
--      Se quitan las tildes para que cada pais quede una sola vez.
--   7. Alcance: el trafico "E" (Especial) son vuelos entre dos paises extranjeros
--      (por ejemplo Panama - La Habana). Tampoco cuentan 10 filas de carga marcadas
--      como internacionales que no tocan Colombia (por ejemplo Montevideo - Ezeiza).
--      Quedan en la tabla con es_colombia = false y las consultas las excluyen.
--
-- No se borran filas repetidas: 73 combinaciones de aerolinea, mes, ruta y tipo
-- de vuelo aparecen dos veces, a veces con cifras distintas (reportes separados).
-- Se dejan como vienen para que los totales cuadren con la fuente; ver REVISION.md.

-- Nombres de ciudad: forma corta para mostrar en el tablero
create or replace table ciudad_corta as
select * from (values
    ('BOGOTA, D.C.',          'BOGOTA'),
    ('SANTIAGO DE CALI',      'CALI'),
    ('SAN JOSE DE CUCUTA',    'CUCUTA'),
    ('CARTAGENA DE INDIAS',   'CARTAGENA'),
    ('RIONEGRO - ANTIOQUIA',  'RIONEGRO'),
    ('SAN ANDRES - ISLA',     'SAN ANDRES'),
    ('SAN ANDRES DE TUMACO',  'TUMACO'),
    ('EL YOPAL',              'YOPAL'),
    ('MEXICO',                'CIUDAD DE MEXICO'),
    ('TIGUANA',               'TIJUANA'),
    ('DALAS',                 'DALLAS'),
    ('EZEIZA',                'BUENOS AIRES'),
    ('INIRIDA',               'PUERTO INIRIDA')
) t(original, corta);

-- Aeropuertos que sirven a una ciudad distinta de la que dice su municipio
create or replace table aeropuerto_etiqueta as
select * from (values
    ('MDE', 'MEDELLIN (RIONEGRO)'),
    ('EOH', 'MEDELLIN (OLAYA HERRERA)')
) t(codigo, etiqueta);

-- Tabla limpia de Origen-Destino: una fila por aerolinea, mes, ruta, trafico y tipo de vuelo
create or replace table od as
select
    try_cast(a_o as integer)                                   as anio,
    try_cast(n_mero_de_mes as integer)                         as mes,
    make_date(try_cast(a_o as integer), try_cast(n_mero_de_mes as integer), 1) as fecha_mes,
    upper(trim(sigla_empresa))                                 as sigla,
    upper(trim(origen))                                        as origen,
    upper(strip_accents(trim(pais_origen)))                    as pais_origen,
    upper(trim(destino))                                       as destino,
    upper(strip_accents(trim(pais_destino)))                   as pais_destino,
    case tr_fico_n_i when 'N' then 'Nacional' when 'I' then 'Internacional'
                     when 'E' then 'Especial' end              as trafico,
    case tipo_vuelo when 'R' then 'Regular' when 'T' then 'Taxi aereo'
                    when 'C' then 'Charter' when 'A' then 'Adicional'
                    when 'N' then 'No regular' end             as tipo_vuelo,
    coalesce(try_cast(pasajeros as bigint), 0)                 as pasajeros,
    pasajeros is null                                          as pasajeros_vacio,
    coalesce(try_cast(carga_correo_kg as double), 0)           as carga_kg,
    tr_fico_n_i in ('N', 'I')
        and 'COLOMBIA' in (upper(strip_accents(trim(pais_origen))),
                           upper(strip_accents(trim(pais_destino)))) as es_colombia,
    -- ciudad cruda sin tildes (para armar la tabla de aeropuertos)
    upper(strip_accents(trim(ciudad_origen)))                  as ciudad_origen_cruda,
    upper(strip_accents(trim(ciudad_destino)))                 as ciudad_destino_cruda,
    trim(nombre)                                               as nombre_reportado
from crudo_od;

-- Aeropuertos: un codigo + pais con su ciudad mas frecuente
create or replace table aeropuertos as
with apariciones as (
    select origen as codigo, pais_origen as pais, ciudad_origen_cruda as ciudad from od where es_colombia
    union all
    select destino, pais_destino, ciudad_destino_cruda from od where es_colombia
),
conteo as (
    select codigo, pais, ciudad, count(*) as n
    from apariciones
    group by codigo, pais, ciudad
),
-- el nombre mas usado; si empatan, el primero en orden alfabetico (igual que en Power Query)
moda as (
    select codigo, pais, ciudad as ciudad_cruda, sum(n) over (partition by codigo, pais) as filas
    from conteo
    qualify row_number() over (partition by codigo, pais order by n desc, ciudad) = 1
)
select
    m.codigo,
    m.pais,
    coalesce(c.corta, m.ciudad_cruda)                     as ciudad,
    coalesce(e.etiqueta, coalesce(c.corta, m.ciudad_cruda)) as etiqueta,
    m.filas
from moda m
left join ciudad_corta c on c.original = m.ciudad_cruda
left join aeropuerto_etiqueta e on e.codigo = m.codigo;

-- Aerolineas: nombre del ultimo mes reportado por cada sigla OACI
create or replace table aerolineas as
select
    sigla,
    arg_max(nombre_reportado, anio * 100 + mes) as nombre,
    min(fecha_mes)                              as primer_mes,
    max(fecha_mes)                              as ultimo_mes
from od
group by sigla;

-- Marca comercial de las aerolineas grandes (el nombre legal no siempre es el que
-- conoce el pasajero). Lista corta y revisada a mano; el resto usa su nombre legal.
create or replace table marca_aerolinea as
select * from (values
    ('AVA', 'Avianca',             'Grupo Avianca'),
    ('AVR', 'Avianca Express',     'Grupo Avianca'),
    ('TPA', 'Avianca Cargo',       'Grupo Avianca'),
    ('LAE', 'LATAM Cargo Colombia','Grupo LATAM'),
    ('GLG', 'Avianca Ecuador',     'Grupo Avianca'),
    ('LRC', 'Avianca Costa Rica',  'Grupo Avianca'),
    ('ARE', 'LATAM Colombia',      'Grupo LATAM'),
    ('LAN', 'LATAM Airlines',      'Grupo LATAM'),
    ('LPE', 'LATAM Peru',          'Grupo LATAM'),
    ('RPB', 'Wingo',               'Wingo'),
    ('VVC', 'Viva Air',            'Viva Air'),
    ('EFY', 'EasyFly',             'EasyFly'),
    ('JEC', 'JetSMART',            'JetSMART'),
    ('NSE', 'Satena',              'Satena'),
    ('ULS', 'Ultra Air',           'Ultra Air'),
    ('CMP', 'Copa Airlines',       'Copa'),
    ('AAL', 'American Airlines',   'American Airlines'),
    ('NKS', 'Spirit Airlines',     'Spirit Airlines')
) t(sigla, marca, grupo);

-- Vista de trabajo: solo trafico de Colombia, con nombres listos
create or replace view v_od as
select
    od.*,
    ao.etiqueta as ciudad_o,
    ad.etiqueta as ciudad_d,
    coalesce(m.marca, a.nombre) as aerolinea,
    coalesce(m.grupo, coalesce(m.marca, a.nombre)) as grupo,
    -- ruta sin direccion: Bogota-Medellin y Medellin-Bogota son la misma ruta
    least(od.origen, od.destino) || '-' || greatest(od.origen, od.destino) as ruta
from od
left join aeropuertos ao on ao.codigo = od.origen  and ao.pais = od.pais_origen
left join aeropuertos ad on ad.codigo = od.destino and ad.pais = od.pais_destino
left join aerolineas a on a.sigla = od.sigla
left join marca_aerolinea m on m.sigla = od.sigla
where od.es_colombia;

-- Nombre de cada ruta (sin direccion), con la ciudad de cada extremo
create or replace table rutas as
select
    ruta,
    any_value(case when origen = least(origen, destino) then ciudad_o else ciudad_d end) as ciudad_a,
    any_value(case when origen = least(origen, destino) then ciudad_d else ciudad_o end) as ciudad_b,
    any_value(trafico) as trafico
from v_od
group by ruta;

-- Tabla limpia de Trafico por Equipo (para vuelos, sillas y ocupacion)
create or replace table eq as
select
    try_cast(a_o as integer)                         as anio,
    try_cast(mes as integer)                         as mes,
    make_date(try_cast(a_o as integer), try_cast(mes as integer), 1) as fecha_mes,
    upper(trim(sigla_empresa))                       as sigla,
    upper(trim(origen))                              as origen,
    upper(trim(destino))                             as destino,
    least(upper(trim(origen)), upper(trim(destino))) || '-' ||
        greatest(upper(trim(origen)), upper(trim(destino))) as ruta,
    upper(trim(tipo_de_equipo))                      as equipo,
    case tr_fico when 'N' then 'Nacional' when 'I' then 'Internacional'
                 when 'E' then 'Especial' end        as trafico,
    case tipo_vuelo when 'R' then 'Regular' when 'T' then 'Taxi aereo'
                    when 'C' then 'Charter' when 'A' then 'Adicional'
                    when 'N' then 'No regular' end   as tipo_vuelo,
    coalesce(try_cast(n_mero_de_vuelos as bigint), 0)     as vuelos,
    coalesce(try_cast(horas_bloque as double), 0)         as horas_bloque,
    coalesce(try_cast(sillas_ofrecidas as bigint), 0)     as sillas,
    coalesce(try_cast(pasajeros_a_bordo as bigint), 0)    as pasajeros_a_bordo,
    coalesce(try_cast(carga_ofrecida_kg as double), 0)    as carga_ofrecida_kg,
    coalesce(try_cast(carga_correo_a_bordo_kg as double), 0) as carga_a_bordo_kg,
    tr_fico in ('N', 'I')
        and 'COLOMBIA' in (upper(strip_accents(trim(pais_origen))),
                           upper(strip_accents(trim(pais_destino)))) as es_colombia
from crudo_eq;
