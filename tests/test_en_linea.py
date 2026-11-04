"""Compara la copia fija contra la API de datos.gov.co EN VIVO.

No corre por defecto (necesita internet). Para correrla:
    python -m pytest -m en_linea

Si falla, Aerocivil corrigio cifras de meses que ya estaban publicados
(pasa: 2022 a 2025 son provisionales). Se actualiza con:
    python scripts/descargar_datos.py
y se vuelven a correr las consultas y las pruebas.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import descargar_datos as dd  # noqa: E402

pytestmark = pytest.mark.en_linea

# Solo el periodo de la copia: si la API ya trae meses nuevos, no cuentan aqui
PERIODO = {"origen_destino": "a_o < 2026 or n_mero_de_mes <= 6", "equipo": "a_o < 2026 or mes <= 6"}


@pytest.mark.parametrize("conjunto", ["origen_destino", "equipo"])
def test_la_fuente_no_cambio(descarga, conjunto):
    id_, col_anio, columnas = dd.CONJUNTOS[conjunto]
    sumas = ", ".join(f"sum({c}) as {c}" for c in columnas)
    try:
        filas = dd.consultar(id_, select=f"{col_anio}, count(*) as filas, {sumas}",
                             where=PERIODO[conjunto], group=col_anio, limit="100")
    except OSError as e:  # sin internet o la API caida: no es un error de los datos
        pytest.skip(f"No se pudo consultar la API: {e}")
    en_vivo = {f[col_anio]: {k: float(v) for k, v in f.items() if k != col_anio} for f in filas}
    guardado = descarga["conjuntos"][conjunto]["totales_api_por_anio"]
    for anio, valores in guardado.items():
        for k, v in valores.items():
            assert en_vivo[anio][k] == pytest.approx(v, abs=0.01), f"{conjunto} {anio} {k}"
