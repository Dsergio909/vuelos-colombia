"""La copia fija cuadra con los totales que calculo la propia API de datos.gov.co."""
from __future__ import annotations

import pytest

ANIOS = [str(a) for a in range(2020, 2027)]


def test_filas_totales(con, descarga):
    for tabla, conjunto in (("crudo_od", "origen_destino"), ("crudo_eq", "equipo")):
        esperadas = sum(v["filas"] for v in descarga["conjuntos"][conjunto]["totales_api_por_anio"].values())
        assert con.execute(f"select count(*) from {tabla}").fetchone()[0] == esperadas


def test_478010_filas_origen_destino(con):
    # Cifra comprobada a mano en datos.gov.co el 4-nov-2026
    assert con.execute("select count(*) from crudo_od").fetchone()[0] == 478_010


@pytest.mark.parametrize("anio", ANIOS)
def test_origen_destino_por_anio(con, descarga, anio):
    api = descarga["conjuntos"]["origen_destino"]["totales_api_por_anio"][anio]
    filas, pax, carga = con.execute(
        "select count(*), sum(pasajeros), sum(carga_kg) from od where anio = ?", [int(anio)]
    ).fetchone()
    assert filas == api["filas"]
    assert pax == api["pasajeros"]
    assert carga == pytest.approx(api["carga_correo_kg"], abs=0.01)


@pytest.mark.parametrize("anio", ANIOS)
def test_equipo_por_anio(con, descarga, anio):
    api = descarga["conjuntos"]["equipo"]["totales_api_por_anio"][anio]
    vuelos, sillas, pax, carga = con.execute(
        "select sum(vuelos), sum(sillas), sum(pasajeros_a_bordo), sum(carga_a_bordo_kg) "
        "from eq where anio = ?", [int(anio)]
    ).fetchone()
    assert vuelos == api["n_mero_de_vuelos"]
    assert sillas == api["sillas_ofrecidas"]
    assert pax == api["pasajeros_a_bordo"]
    assert carga == pytest.approx(api["carga_correo_a_bordo_kg"], abs=0.01)


def test_periodo_enero_2020_a_junio_2026(con):
    for tabla in ("od", "eq"):
        desde, hasta = con.execute(f"select min(fecha_mes), max(fecha_mes) from {tabla}").fetchone()
        assert (desde.isoformat(), hasta.isoformat()) == ("2020-01-01", "2026-06-01")
