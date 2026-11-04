"""Descarga los dos conjuntos de Aerocivil desde datos.gov.co (API Socrata).

Uso:
    python scripts/descargar_datos.py             # baja todo y arma la copia fija
    python scripts/descargar_datos.py --sin-bajar # solo rehace la copia fija desde datos/crudos

Que hace:
1. Baja los datos por paginas de 50.000 filas, en orden fijo (:id), a datos/crudos/ (CSV).
   Esa carpeta no se sube a GitHub (pesa unos 100 MB).
2. Los pasa a Parquet en datos/fuente/ (unos 6 MB). Esa es la copia fija que usan
   las consultas y las pruebas, para que los resultados no cambien solos.
3. Le pide a la API los totales por año (filas, pasajeros, carga) y los guarda en
   datos/fuente/descarga.json. Las pruebas comparan la copia contra esos totales.

No pide clave ni registro.
Fuente: Unidad Administrativa Especial de Aeronautica Civil (Aerocivil),
publicado en datos.gov.co con licencia CC BY-SA 4.0.
"""
from __future__ import annotations

import csv
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CRUDOS = RAIZ / "datos" / "crudos"
FUENTE = RAIZ / "datos" / "fuente"
API = "https://www.datos.gov.co/resource/{id}.{fmt}"
PAGINA = 50_000
REINTENTOS = 4

# nombre local -> (id en datos.gov.co, columna de año, columnas numericas a sumar)
CONJUNTOS = {
    "origen_destino": ("gb6w-ynu4", "a_o", ["pasajeros", "carga_correo_kg"]),
    "equipo": ("djjf-g4q4", "a_o", ["n_mero_de_vuelos", "sillas_ofrecidas",
                                    "pasajeros_a_bordo", "carga_correo_a_bordo_kg"]),
}


def _get(url: str) -> bytes:
    """GET con reintentos y espera creciente (la API a veces corta la conexion)."""
    for intento in range(1, REINTENTOS + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "vuelos-colombia/1.0"})
            with urllib.request.urlopen(req, timeout=120) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if intento == REINTENTOS:
                raise
            espera = 5 * intento
            print(f"  fallo ({e}); reintento {intento} en {espera} s", flush=True)
            time.sleep(espera)
    raise RuntimeError("inalcanzable")


def consultar(id_: str, **params: str) -> list[dict]:
    q = urllib.parse.urlencode({f"${k}": v for k, v in params.items()})
    return json.loads(_get(f"{API.format(id=id_, fmt='json')}?{q}"))


def totales_por_anio(id_: str, col_anio: str, columnas: list[str]) -> dict[str, dict]:
    """Totales oficiales por año, calculados por la propia API."""
    sumas = ", ".join(f"sum({c}) as {c}" for c in columnas)
    filas = consultar(id_, select=f"{col_anio}, count(*) as filas, {sumas}",
                      group=col_anio, order=col_anio, limit="100")
    return {f[col_anio]: {k: float(v) for k, v in f.items() if k != col_anio} for f in filas}


def descargar(nombre: str, id_: str) -> int:
    CRUDOS.mkdir(parents=True, exist_ok=True)
    destino = CRUDOS / f"{nombre}.csv"
    esperadas = int(consultar(id_, select="count(*)")[0]["count"])
    print(f"{nombre} ({id_}): la API reporta {esperadas:,} filas", flush=True)

    escritas = 0
    encabezado = None
    with destino.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        offset = 0
        while True:
            q = urllib.parse.urlencode({"$limit": PAGINA, "$offset": offset, "$order": ":id"})
            texto = _get(f"{API.format(id=id_, fmt='csv')}?{q}").decode("utf-8")
            filas = list(csv.reader(io.StringIO(texto)))
            if encabezado is None:
                encabezado = filas[0]
                w.writerow(encabezado)
            elif filas[0] != encabezado:
                raise RuntimeError("El encabezado cambio entre paginas")
            datos = filas[1:]
            w.writerows(datos)
            escritas += len(datos)
            offset += PAGINA
            print(f"  {escritas:,} filas", flush=True)
            if len(datos) < PAGINA:
                break

    if escritas != esperadas:
        raise RuntimeError(f"{nombre}: se bajaron {escritas} filas y la API dice {esperadas}")
    return escritas


def a_parquet(nombre: str) -> None:
    import duckdb  # solo se necesita en este paso

    FUENTE.mkdir(parents=True, exist_ok=True)
    origen = (CRUDOS / f"{nombre}.csv").as_posix()
    destino = (FUENTE / f"{nombre}.parquet").as_posix()
    # all_varchar: se guarda tal cual, como texto. Los tipos se ponen en sql/02_limpiar.sql
    duckdb.sql(f"copy (select * from read_csv('{origen}', all_varchar=true)) "
               f"to '{destino}' (format parquet, compression zstd, compression_level 19)")


def main() -> int:
    sin_bajar = "--sin-bajar" in sys.argv
    resumen = {
        "fuente": "Aerocivil, datos.gov.co, licencia CC BY-SA 4.0",
        "descargado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "conjuntos": {},
    }
    for nombre, (id_, col_anio, columnas) in CONJUNTOS.items():
        if not sin_bajar:
            descargar(nombre, id_)
        a_parquet(nombre)
        resumen["conjuntos"][nombre] = {
            "id": id_,
            "url": f"https://www.datos.gov.co/d/{id_}",
            "totales_api_por_anio": totales_por_anio(id_, col_anio, columnas),
        }
    if sin_bajar:
        anterior = CRUDOS / "descarga.json"
        if anterior.exists():
            resumen["descargado_utc"] = json.loads(anterior.read_text(encoding="utf-8"))["descargado_utc"]
    (FUENTE / "descarga.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    print("Listo: datos/fuente/descarga.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
