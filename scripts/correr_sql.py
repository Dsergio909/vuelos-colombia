"""Corre las consultas de sql/ en orden y guarda los resultados.

Uso:
    python scripts/correr_sql.py

1. Arma la base datos/vuelos.duckdb con 01_cargar.sql y 02_limpiar.sql.
2. Corre cada consulta de analisis (10 en adelante). La ultima sentencia de cada
   archivo es un SELECT: su resultado se guarda en resultados/<archivo>.csv.

Se puede correr desde cualquier carpeta: las rutas salen de la raiz del repo.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parent.parent
SQL = RAIZ / "sql"
RESULTADOS = RAIZ / "resultados"
BASE = RAIZ / "datos" / "vuelos.duckdb"


def conectar(base: Path | str = BASE) -> duckdb.DuckDBPyConnection:
    """Abre la base y deja la carpeta de trabajo en la raiz del repo."""
    os.chdir(RAIZ)
    return duckdb.connect(str(base))


def construir(con: duckdb.DuckDBPyConnection) -> None:
    for nombre in ("01_cargar.sql", "02_limpiar.sql"):
        con.execute((SQL / nombre).read_text(encoding="utf-8"))


def consultas_de_analisis() -> list[Path]:
    return sorted(p for p in SQL.glob("*.sql") if int(p.name[:2]) >= 10)


def ultima_consulta(con: duckdb.DuckDBPyConnection, archivo: Path) -> str:
    """Corre todo el archivo menos la ultima sentencia y devuelve esa ultima (el SELECT)."""
    sentencias = duckdb.extract_statements(archivo.read_text(encoding="utf-8"))
    for s in sentencias[:-1]:
        con.execute(s.query)
    return sentencias[-1].query.strip().rstrip(";")


def main() -> int:
    RESULTADOS.mkdir(exist_ok=True)
    con = conectar()
    construir(con)
    for archivo in consultas_de_analisis():
        consulta = ultima_consulta(con, archivo)
        destino = RESULTADOS / f"{archivo.stem}.csv"
        con.execute(f"copy ({consulta}) to '{destino.as_posix()}' (header, delimiter ',')")
        n = con.execute(f"select count(*) from ({consulta})").fetchone()[0]
        print(f"{archivo.name}: {n} filas -> resultados/{destino.name}")
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
