-- 01_cargar.sql
-- Carga la copia fija de los dos conjuntos de Aerocivil, tal como vienen de la API:
-- todas las columnas como texto, sin tocar nada. La limpieza va en 02_limpiar.sql.
--
-- Fuente: Aerocivil en datos.gov.co, licencia CC BY-SA 4.0
--   gb6w-ynu4  Transporte Aereo Comercial - Trafico Origen-Destino
--   djjf-g4q4  Transporte Aereo - Trafico por Equipo

create or replace table crudo_od as
select * from read_parquet('datos/fuente/origen_destino.parquet');

create or replace table crudo_eq as
select * from read_parquet('datos/fuente/equipo.parquet');
