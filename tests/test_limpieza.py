"""La limpieza no pierde ni inventa datos."""
from __future__ import annotations


def test_ningun_tipo_falla(con):
    # Todo año, mes y carga se pudo leer; los unicos vacios son los 52 de pasajeros
    malos = con.execute("""
        select count(*) filter (where anio is null or mes is null or fecha_mes is null),
               count(*) filter (where trafico is null or tipo_vuelo is null)
        from od
    """).fetchone()
    assert malos == (0, 0)
    assert con.execute("select count(*) from crudo_od where try_cast(carga_correo_kg as double) is null").fetchone()[0] == 0


def test_pasajeros_vacios_marcados(con):
    vacios = con.execute("select count(*) from crudo_od where pasajeros is null").fetchone()[0]
    marcados = con.execute("select count(*) from od where pasajeros_vacio and pasajeros = 0").fetchone()[0]
    assert vacios == marcados == 52


def test_sin_negativos(con):
    assert con.execute("select count(*) from od where pasajeros < 0 or carga_kg < 0").fetchone()[0] == 0
    assert con.execute(
        "select count(*) from eq where vuelos < 0 or sillas < 0 or pasajeros_a_bordo < 0"
    ).fetchone()[0] == 0


def test_alcance_colombia(con):
    # Fuera: el trafico Especial (entre dos paises extranjeros) y 10 filas de carga
    # marcadas como internacionales que no tocan Colombia. Nada mas.
    total = con.execute("select count(*) from od").fetchone()[0]
    colombia = con.execute("select count(*) from v_od").fetchone()[0]
    especial = con.execute("select count(*) from od where trafico = 'Especial'").fetchone()[0]
    sin_colombia = con.execute(
        "select count(*) from od where trafico <> 'Especial' and 'COLOMBIA' not in (pais_origen, pais_destino)"
    ).fetchone()[0]
    assert (especial, sin_colombia) == (12_240, 10)
    assert colombia + especial + sin_colombia == total
    assert con.execute("select sum(pasajeros) from od where trafico <> 'Especial' and not es_colombia").fetchone()[0] == 0


def test_paises_sin_tildes_duplicadas(con):
    # "PANAMA" y "PANAMÁ" deben quedar como un solo pais
    assert con.execute(
        "select count(*) from (select distinct pais_origen from od) where pais_origen <> strip_accents(pais_origen)"
    ).fetchone()[0] == 0


def test_la_vista_no_duplica_filas(con):
    # Los cruces con aeropuertos y aerolineas no pueden multiplicar filas ni pasajeros
    a = con.execute("select count(*), sum(pasajeros) from od where es_colombia").fetchone()
    b = con.execute("select count(*), sum(pasajeros) from v_od").fetchone()
    assert a == b


def test_aeropuertos_y_aerolineas_unicos(con):
    assert con.execute(
        "select count(*) from (select codigo, pais from aeropuertos group by all having count(*) > 1)"
    ).fetchone()[0] == 0
    assert con.execute(
        "select count(*) from (select sigla from aerolineas group by all having count(*) > 1)"
    ).fetchone()[0] == 0


def test_todas_las_filas_tienen_ciudad_y_aerolinea(con):
    sin_nombre = con.execute(
        "select count(*) from v_od where ciudad_o is null or ciudad_d is null or aerolinea is null"
    ).fetchone()[0]
    assert sin_nombre == 0


def test_cada_ruta_tiene_un_solo_nombre(con):
    assert con.execute("select count(*) - count(distinct ruta) from rutas").fetchone()[0] == 0


def test_marcas_existen_en_los_datos(con):
    # Cada sigla de la lista de marcas debe existir; si no, la lista quedo vieja
    huerfanas = con.execute(
        "select list(sigla) from marca_aerolinea where sigla not in (select sigla from aerolineas)"
    ).fetchone()[0]
    assert huerfanas in (None, [])
