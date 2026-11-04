"""Arma datos/referencia/aeropuertos_coordenadas.csv para el mapa del tablero.

Uso:
    python scripts/coordenadas_aeropuertos.py

Los datos de Aerocivil no traen latitud ni longitud. Este script baja la base
publica de OurAirports (dominio publico, https://ourairports.com/data/) y toma
las coordenadas de cada aeropuerto por su codigo IATA.

Regla para no poner un punto en el pais equivocado: el codigo solo se acepta si
el pais coincide (Colombia con CO, y un aeropuerto extranjero con un pais que no
sea CO). Los codigos locales de pistas pequeñas (por ejemplo 7IY) no son IATA y
quedan sin coordenadas: no salen en el mapa, pero sus pasajeros si cuentan.
"""
from __future__ import annotations

import csv
import io
import sys
import urllib.request
from pathlib import Path

import duckdb

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
import correr_sql  # noqa: E402

URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"
DESTINO = RAIZ / "datos" / "referencia" / "aeropuertos_coordenadas.csv"


def main() -> int:
    req = urllib.request.Request(URL, headers={"User-Agent": "vuelos-colombia/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        texto = r.read().decode("utf-8")
    por_iata: dict[str, list[dict]] = {}
    for fila in csv.DictReader(io.StringIO(texto)):
        if fila["iata_code"]:
            por_iata.setdefault(fila["iata_code"].upper(), []).append(fila)

    con = correr_sql.conectar(":memory:")
    correr_sql.construir(con)
    aeropuertos = con.execute("select codigo, pais, ciudad, etiqueta from aeropuertos order by codigo, pais").fetchall()

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    con_coord = 0
    with DESTINO.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["codigo", "pais", "latitud", "longitud", "nombre_ourairports"])
        for codigo, pais, _ciudad, _etiqueta in aeropuertos:
            candidatos = [c for c in por_iata.get(codigo, [])
                          if (c["iso_country"] == "CO") == (pais == "COLOMBIA")]
            if len(candidatos) != 1:
                continue
            c = candidatos[0]
            w.writerow([codigo, pais, round(float(c["latitude_deg"]), 4),
                        round(float(c["longitude_deg"]), 4), c["name"]])
            con_coord += 1
    print(f"{con_coord} de {len(aeropuertos)} aeropuertos con coordenadas -> {DESTINO.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
