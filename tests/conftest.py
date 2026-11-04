"""Arma una base DuckDB en memoria con la copia fija y la comparte entre pruebas."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

import correr_sql  # noqa: E402


@pytest.fixture(scope="session")
def con():
    c = correr_sql.conectar(":memory:")
    correr_sql.construir(c)
    yield c
    c.close()


@pytest.fixture(scope="session")
def descarga() -> dict:
    return json.loads((RAIZ / "datos" / "fuente" / "descarga.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="session")
def resultado(con):
    """Corre una consulta de sql/ (por su numero) y devuelve sus filas como dicts."""
    def _correr(numero: str) -> list[dict]:
        archivo = next((RAIZ / "sql").glob(f"{numero}_*.sql"))
        rel = con.execute(correr_sql.ultima_consulta(con, archivo))
        cols = [d[0] for d in rel.description]
        return [dict(zip(cols, f)) for f in rel.fetchall()]
    return _correr
