-- 99_cifras_clave.sql
-- Las cifras que cita el README, calculadas aqui y en ningun otro lado.
-- La prueba tests/test_readme.py revisa que cada una aparezca tal cual en
-- README.md y README.en.md, para que el README no tenga cifras inventadas.
-- Cada cifra va redondeada como se escribe en el texto.

with
pax as (
    select anio, trafico, sum(pasajeros) as p
    from v_od group by all
),
grupos as (
    select anio, grupo, 100.0 * sum(pasajeros) / sum(sum(pasajeros)) over (partition by anio) as pct
    from v_od where trafico = 'Nacional' group by anio, grupo
),
hhi as (
    select anio, sum(pct * pct) as hhi from grupos group by anio
),
bog as (
    select anio, (origen = 'BOG' or destino = 'BOG') as pasa_bog, sum(pasajeros) as p
    from v_od where trafico = 'Nacional' group by all
),
mensual as (
    select anio, mes, sum(pasajeros) as p
    from v_od where trafico = 'Nacional' and anio between 2022 and 2025 group by all
),
indice_mes as (
    select mes, avg(idx) as idx
    from (select mes, 100.0 * p / avg(p) over (partition by anio) as idx from mensual)
    group by mes
),
carga_sale as (
    select anio, mes, sum(carga_kg) as kg
    from v_od where trafico = 'Internacional' and pais_origen = 'COLOMBIA' and anio between 2022 and 2025
    group by all
),
indice_carga as (
    select mes, avg(idx) as idx
    from (select mes, 100.0 * kg / avg(kg) over (partition by anio) as idx from carga_sale)
    group by mes
),
ocupacion as (
    select anio, 100.0 * sum(pasajeros_a_bordo) / sum(sillas) as pct
    from eq where es_colombia and trafico = 'Nacional' and tipo_vuelo = 'Regular' and sillas > 0
    group by anio
),
f(clave, valor, decimales) as (
    -- 1. El crecimiento vino de lo internacional
    select 'nacional_2022_millones', (select p from pax where anio = 2022 and trafico = 'Nacional') / 1e6, 1
    union all select 'nacional_2025_millones', (select p from pax where anio = 2025 and trafico = 'Nacional') / 1e6, 1
    union all select 'nacional_variacion_2022_2025_pct',
        100.0 * ((select p from pax where anio = 2025 and trafico = 'Nacional')
               / (select p from pax where anio = 2022 and trafico = 'Nacional') - 1), 1
    union all select 'internacional_2022_millones', (select p from pax where anio = 2022 and trafico = 'Internacional') / 1e6, 1
    union all select 'internacional_2025_millones', (select p from pax where anio = 2025 and trafico = 'Internacional') / 1e6, 1
    union all select 'internacional_variacion_2022_2025_pct',
        100.0 * ((select p from pax where anio = 2025 and trafico = 'Internacional')
               / (select p from pax where anio = 2022 and trafico = 'Internacional') - 1), 1
    union all select 'internacional_participacion_2022_pct',
        100.0 * (select p from pax where anio = 2022 and trafico = 'Internacional')
              / (select sum(p) from pax where anio = 2022), 1
    union all select 'internacional_participacion_2025_pct',
        100.0 * (select p from pax where anio = 2025 and trafico = 'Internacional')
              / (select sum(p) from pax where anio = 2025), 1
    -- 2. Concentracion del mercado nacional
    union all select 'avianca_latam_2022_pct', (select sum(pct) from grupos where anio = 2022 and grupo in ('Grupo Avianca', 'Grupo LATAM')), 1
    union all select 'avianca_latam_2023_pct', (select sum(pct) from grupos where anio = 2023 and grupo in ('Grupo Avianca', 'Grupo LATAM')), 1
    union all select 'avianca_latam_2025_pct', (select sum(pct) from grupos where anio = 2025 and grupo in ('Grupo Avianca', 'Grupo LATAM')), 1
    union all select 'viva_ultra_2022_pct', (select sum(pct) from grupos where anio = 2022 and grupo in ('Viva Air', 'Ultra Air')), 1
    union all select 'jetsmart_2025_pct', (select pct from grupos where anio = 2025 and grupo = 'JetSMART'), 1
    union all select 'hhi_2022', (select hhi from hhi where anio = 2022), 0
    union all select 'hhi_2023', (select hhi from hhi where anio = 2023), 0
    union all select 'hhi_2025', (select hhi from hhi where anio = 2025), 0
    -- 3. Bogota y las rutas punto a punto
    union all select 'ruta_bog_mde_2025_millones',
        (select sum(pasajeros) from v_od where anio = 2025 and ruta = 'BOG-MDE') / 1e6, 1
    union all select 'pasa_por_bogota_2025_pct',
        100.0 * (select p from bog where anio = 2025 and pasa_bog) / (select sum(p) from bog where anio = 2025), 1
    union all select 'punto_a_punto_variacion_2022_2024_pct',
        100.0 * ((select p from bog where anio = 2024 and not pasa_bog) / (select p from bog where anio = 2022 and not pasa_bog) - 1), 1
    union all select 'punto_a_punto_variacion_2025_pct',
        100.0 * ((select p from bog where anio = 2025 and not pasa_bog) / (select p from bog where anio = 2024 and not pasa_bog) - 1), 1
    union all select 'pasa_por_bogota_variacion_2025_pct',
        100.0 * ((select p from bog where anio = 2025 and pasa_bog) / (select p from bog where anio = 2024 and pasa_bog) - 1), 1
    -- 4. Temporadas (indice 100 = mes normal, promedio 2022-2025)
    union all select 'indice_diciembre_nacional', (select idx from indice_mes where mes = 12), 1
    union all select 'indice_febrero_nacional', (select idx from indice_mes where mes = 2), 1
    union all select 'diciembre_contra_febrero_pct',
        100.0 * ((select idx from indice_mes where mes = 12) / (select idx from indice_mes where mes = 2) - 1), 0
    -- 5. Carga
    union all select 'carga_internacional_2025_pct',
        100.0 * (select sum(carga_kg) from v_od where anio = 2025 and trafico = 'Internacional')
              / (select sum(carga_kg) from v_od where anio = 2025), 1
    union all select 'carga_bog_mia_2025_pct',
        100.0 * (select sum(carga_kg) from v_od where anio = 2025 and ruta = 'BOG-MIA')
              / (select sum(carga_kg) from v_od where anio = 2025 and trafico = 'Internacional'), 1
    union all select 'indice_carga_sale_abril', (select idx from indice_carga where mes = 4), 1
    union all select 'ocupacion_nacional_2025_pct', (select pct from ocupacion where anio = 2025), 1
    -- 6. 2026 y el pronostico de julio a diciembre (sql/19_pronostico.sql)
    union all select 'nacional_s1_2026_variacion_pct',
        100.0 * ((select sum(pasajeros) from v_od where trafico = 'Nacional' and anio = 2026 and mes <= 6)
               / (select sum(pasajeros) from v_od where trafico = 'Nacional' and anio = 2025 and mes <= 6) - 1), 1
    union all select 'pronostico_error_nacional_pct',
        (select avg(100.0 * abs(pronostico - real) / real) from pronostico where anio = 2025 and trafico = 'Nacional'), 1
    union all select 'pronostico_error_internacional_pct',
        (select avg(100.0 * abs(pronostico - real) / real) from pronostico where anio = 2025 and trafico = 'Internacional'), 1
    union all select 'pronostico_nacional_s2_2026_millones',
        (select sum(pronostico) from pronostico where anio = 2026 and trafico = 'Nacional') / 1e6, 1
)
select clave, round(valor, decimales) as valor, decimales
from f;
