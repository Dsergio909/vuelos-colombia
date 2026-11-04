"""Los resultados de las consultas son coherentes entre si y con los datos."""
from __future__ import annotations

import pytest


def test_resumen_anual_suma_nacional_mas_internacional(resultado, con):
    for f in resultado("10"):
        assert f["pasajeros"] == f["pasajeros_nacionales"] + f["pasajeros_internacionales"]
    total = con.execute("select sum(pasajeros) from v_od").fetchone()[0]
    assert sum(f["pasajeros"] for f in resultado("10")) == total


def test_rutas_sin_direccion_suman_los_dos_sentidos(resultado, con):
    top = next(f for f in resultado("11") if f["trafico"] == "Nacional" and f["puesto"] == 1)
    a, b = top["ruta"].split("-")
    ida_y_vuelta = con.execute(
        "select sum(pasajeros) from v_od where anio = 2025 and "
        "((origen = ? and destino = ?) or (origen = ? and destino = ?))", [a, b, b, a]
    ).fetchone()[0]
    assert top["pasajeros_2025"] == ida_y_vuelta


def test_participacion_acumulada_crece(resultado):
    for trafico in ("Nacional", "Internacional"):
        filas = [f for f in resultado("11") if f["trafico"] == trafico]
        acumulada = [f["participacion_acumulada_pct"] for f in filas]
        assert acumulada == sorted(acumulada)
        assert 0 < acumulada[-1] <= 100


def test_indice_de_temporada_promedia_100(resultado):
    # El indice de cada año promedia 100 por construccion
    for trafico in ("Nacional", "Internacional"):
        indices = [f["indice_promedio"] for f in resultado("12") if f["trafico"] == trafico]
        assert len(indices) == 12
        assert sum(indices) / 12 == pytest.approx(100, abs=0.1)


def test_participaciones_de_aerolineas_no_pasan_de_100(resultado):
    por_anio: dict[int, float] = {}
    for f in resultado("13"):
        por_anio[f["anio"]] = por_anio.get(f["anio"], 0) + f["participacion_pct"]
        assert 0 < f["hhi_del_anio"] <= 10_000
    assert all(v <= 100.05 for v in por_anio.values())


def test_ocupacion_entre_0_y_100(resultado):
    for f in resultado("16"):
        assert 0 < f["ocupacion_pct"] <= 100


def test_todos_los_controles_de_calidad_pasan(resultado):
    malos = [f["control"] for f in resultado("20") if f["estado"] != "Pasa"]
    assert not malos, malos
