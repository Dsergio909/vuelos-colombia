"""Cada cifra clave del README sale de los datos (sql/18_cifras_clave.sql).

Si alguien cambia una consulta o actualiza los datos, esta prueba avisa que
el README quedo con cifras viejas.
"""
from __future__ import annotations

from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent


def formato(valor: float, decimales: int, idioma: str) -> str:
    """32.7 -> '32,7' (es) o '32.7' (en); 2483 -> '2.483' (es) o '2,483' (en).
    Los negativos se escriben sin signo: el texto dice 'cayo 20,4 %'."""
    texto = f"{abs(valor):,.{int(decimales)}f}"  # formato ingles: 2,483.5
    if idioma == "es":
        texto = texto.replace(",", "_").replace(".", ",").replace("_", ".")
    return texto


def cifras(resultado):
    return [(f["clave"], f["valor"], f["decimales"]) for f in resultado("18")]


@pytest.mark.parametrize("archivo,idioma", [("README.md", "es"), ("README.en.md", "en")])
def test_cifras_del_readme_salen_de_los_datos(resultado, archivo, idioma):
    texto = (RAIZ / archivo).read_text(encoding="utf-8")
    faltan = [f"{clave} = {formato(v, d, idioma)}" for clave, v, d in cifras(resultado)
              if formato(v, d, idioma) not in texto]
    assert not faltan, f"{archivo} no tiene estas cifras (o las tiene distintas): {faltan}"


def test_formato():
    assert formato(2483.0, 0, "es") == "2.483"
    assert formato(2483.0, 0, "en") == "2,483"
    assert formato(-20.4, 1, "es") == "20,4"
    assert formato(32.7, 1, "en") == "32.7"
