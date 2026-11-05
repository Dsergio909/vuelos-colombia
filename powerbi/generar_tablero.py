"""Genera el proyecto de Power BI (formato PBIP, en texto) y dax/medidas.md.

Uso:
    python powerbi/generar_tablero.py

Por que en texto: un .pbix es un archivo binario y en GitHub no se puede leer.
El formato PBIP guarda el modelo (TMDL) y las paginas (PBIR) como archivos de
texto. Este script los arma a partir de:
  - powerquery/*.pq   la limpieza de Power Query (la misma de sql/02_limpiar.sql)
  - MEDIDAS (abajo)   las medidas DAX, que tambien se escriben en dax/medidas.md
  - PAGINAS (abajo)   las cinco paginas del tablero y la de control

Despues se abre powerbi/vuelos-colombia.pbip en Power BI Desktop, se actualiza
y se guarda tambien como .pbix.
"""
from __future__ import annotations

import json
import re
import shutil
import uuid
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PQ = RAIZ / "powerquery"
SALIDA = RAIZ / "powerbi"
NOMBRE = "vuelos-colombia"
MODELO = SALIDA / f"{NOMBRE}.SemanticModel"
INFORME = SALIDA / f"{NOMBRE}.Report"

ACENTO = "#1d4a35"      # verde oscuro del portafolio: el unico color de acento
TEXTO = "#1f2328"
GRIS = "#5b6770"
BORDE = "#e1e4e8"
FONDO_PAGINA = "#f6f7f8"

SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition"


def tag(*partes: str) -> str:
    """lineageTag estable: el mismo nombre da siempre el mismo identificador."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "vuelos-colombia/" + "/".join(partes)))


def q(nombre: str) -> str:
    """Pone comillas simples a los nombres TMDL que las necesitan."""
    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", nombre):
        return nombre
    return "'" + nombre.replace("'", "''") + "'"


# ---------------------------------------------------------------------------
# Modelo: tablas, columnas y relaciones
# ---------------------------------------------------------------------------
# (nombre, tipo, formato, resumen, oculta, extra)
T, I, D, F = "string", "int64", "double", "dateTime"

TABLAS = {
    "Trafico": ("10_Trafico.pq", [
        ("Fecha", F, "mmm yyyy", "none", True, {}),
        ("Sigla", T, None, "none", True, {}),
        ("Ruta", T, None, "none", True, {}),
        ("Clave ruta", T, None, "none", True, {}),
        ("Origen", T, None, "none", True, {}),
        ("Destino", T, None, "none", True, {}),
        ("Clave origen", T, None, "none", True, {}),
        ("Clave destino", T, None, "none", True, {}),
        ("Tráfico", T, None, "none", True, {}),
        ("Tipo de vuelo", T, None, "none", False, {}),
        ("Sentido", T, None, "none", False, {}),
        ("País exterior", T, None, "none", False, {}),
        ("Pasajeros", I, "#,0", "sum", True, {}),
        ("Carga kg", D, "#,0", "sum", True, {}),
    ]),
    "Equipo": ("11_Equipo.pq", [
        ("Fecha", F, "mmm yyyy", "none", True, {}),
        ("Sigla", T, None, "none", True, {}),
        ("Ruta", T, None, "none", True, {}),
        ("Clave ruta", T, None, "none", True, {}),
        ("Tráfico", T, None, "none", True, {}),
        ("Tipo de vuelo", T, None, "none", True, {}),
        ("Vuelos", I, "#,0", "sum", True, {}),
        ("Sillas", I, "#,0", "sum", True, {}),
        ("Pasajeros a bordo", I, "#,0", "sum", True, {}),
        ("Pasajeros con sillas", I, "#,0", "sum", True, {}),
        ("Carga a bordo kg", D, "#,0", "sum", True, {}),
    ]),
    "Aeropuertos": ("20_Aeropuertos.pq", [
        ("Clave", T, None, "none", True, {}),
        ("Código", T, None, "none", False, {}),
        ("País", T, None, "none", False, {}),
        ("Ciudad aeropuerto", T, None, "none", False, {}),
        ("Nombre mapa", T, None, "none", False, {}),
        ("Latitud", D, "0.0000", "none", False, {"dataCategory": "Latitude"}),
        ("Longitud", D, "0.0000", "none", False, {"dataCategory": "Longitude"}),
    ]),
    "Rutas": ("21_Rutas.pq", [
        ("Clave ruta", T, None, "none", True, {}),
        ("Ruta", T, None, "none", False, {}),
        ("Nombre ruta", T, None, "none", False, {}),
        ("Ciudad A", T, None, "none", False, {}),
        ("Ciudad B", T, None, "none", False, {}),
        ("Tráfico de la ruta", T, None, "none", False, {}),
    ]),
    "Aerolineas": ("22_Aerolineas.pq", [
        ("Sigla", T, None, "none", False, {}),
        ("Nombre reportado", T, None, "none", False, {}),
        ("Aerolínea", T, None, "none", False, {}),
        ("Grupo empresarial", T, None, "none", False, {}),
        ("Grupo tablero", T, None, "none", False, {}),
    ]),
    "Calendario": ("23_Calendario.pq", [
        ("Fecha", F, "mmm yyyy", "none", False, {}),
        ("Año", I, "0", "none", False, {}),
        ("Mes", I, "0", "none", True, {}),
        ("Nombre mes", T, None, "none", False, {"sortByColumn": "Mes"}),
        ("Mes largo", T, None, "none", False, {"sortByColumn": "Mes"}),
    ]),
    "TipoTrafico": ("24_TipoTrafico.pq", [
        ("Tráfico", T, None, "none", False, {"sortByColumn": "Orden"}),
        ("Orden", I, "0", "none", True, {}),
    ]),
}

EXPRESIONES = [  # consultas que no se cargan al modelo
    ("CarpetaDatos", "00_CarpetaDatos.pq", "Text"),
    ("fnQuitarTildes", "01_fnQuitarTildes.pq", "Function"),
    ("OD_crudo", "02_OD_crudo.pq", "Table"),
    ("EQ_crudo", "03_EQ_crudo.pq", "Table"),
]

# (desde, hacia, activa)
RELACIONES = [
    ("Trafico.Fecha", "Calendario.Fecha", True),
    ("Equipo.Fecha", "Calendario.Fecha", True),
    ("Trafico.Sigla", "Aerolineas.Sigla", True),
    ("Equipo.Sigla", "Aerolineas.Sigla", True),
    ("Trafico.Clave ruta", "Rutas.Clave ruta", True),
    ("Equipo.Clave ruta", "Rutas.Clave ruta", True),
    ("Trafico.Tráfico", "TipoTrafico.Tráfico", True),
    ("Equipo.Tráfico", "TipoTrafico.Tráfico", True),
    # Aeropuertos juega dos papeles (origen y destino): relaciones inactivas que
    # se encienden con USERELATIONSHIP en la medida "Pasajeros por aeropuerto"
    ("Trafico.Clave origen", "Aeropuertos.Clave", False),
    ("Trafico.Clave destino", "Aeropuertos.Clave", False),
]

# ---------------------------------------------------------------------------
# Medidas DAX: (carpeta, nombre, formato, descripcion, expresion)
# ---------------------------------------------------------------------------
MEDIDAS = [
    ("Base", "Pasajeros", "#,0",
     "Pasajeros de pago (dato de Aerocivil, conjunto Origen-Destino).",
     "SUM ( Trafico[Pasajeros] )"),
    ("Base", "Carga (t)", "#,0",
     "Carga más correo, en toneladas.",
     "DIVIDE ( SUM ( Trafico[Carga kg] ), 1000 )"),
    ("Base", "Pasajeros nacionales", "#,0",
     "Pasajeros de vuelos nacionales. Ignora el filtro de tráfico a propósito.",
     'CALCULATE ( [Pasajeros], TipoTrafico[Tráfico] = "Nacional" )'),
    ("Base", "Pasajeros internacionales", "#,0",
     "Pasajeros de vuelos internacionales (salen o llegan a Colombia).",
     'CALCULATE ( [Pasajeros], TipoTrafico[Tráfico] = "Internacional" )'),
    ("Base", "% internacional", "0.0%",
     "Parte de los pasajeros que vuela fuera del país.",
     "DIVIDE ( [Pasajeros internacionales], [Pasajeros nacionales] + [Pasajeros internacionales] )"),
    ("Comparación", "Pasajeros año anterior", "#,0",
     "Los mismos meses del año anterior. Si se ve 2026 (enero a junio), compara contra enero a junio de 2025.",
     """VAR anio = MAX ( Calendario[Año] )
VAR meses = VALUES ( Calendario[Mes] )
RETURN
    IF (
        HASONEVALUE ( Calendario[Año] ),
        CALCULATE (
            [Pasajeros],
            REMOVEFILTERS ( Calendario ),
            Calendario[Año] = anio - 1,
            TREATAS ( meses, Calendario[Mes] )
        )
    )"""),
    ("Comparación", "Variación vs año anterior", "+0.0%;-0.0%;0.0%",
     "Cambio de pasajeros contra los mismos meses del año anterior.",
     "DIVIDE ( [Pasajeros] - [Pasajeros año anterior], [Pasajeros año anterior] )"),
    ("Aerolíneas", "Participación nacional", "0.0%",
     "Parte de los pasajeros nacionales que lleva cada aerolínea o grupo.",
     "DIVIDE ( [Pasajeros nacionales], CALCULATE ( [Pasajeros nacionales], REMOVEFILTERS ( Aerolineas ) ) )"),
    ("Aerolíneas", "HHI nacional", "#,0",
     "Índice de Herfindahl-Hirschman: suma de las participaciones al cuadrado (de 0 a 10.000). "
     "Más de 2.500 es un mercado muy concentrado. Se calcula por grupo empresarial.",
     """SUMX (
    VALUES ( Aerolineas[Grupo empresarial] ),
    VAR s =
        100
            * DIVIDE (
                CALCULATE ( [Pasajeros nacionales] ),
                CALCULATE ( [Pasajeros nacionales], REMOVEFILTERS ( Aerolineas ) )
            )
    RETURN
        s * s
)"""),
    ("Operación", "Ocupación", "0.0%",
     "Pasajeros a bordo / sillas ofrecidas, en vuelos regulares con sillas reportadas (conjunto Tráfico por Equipo).",
     """DIVIDE (
    CALCULATE ( SUM ( Equipo[Pasajeros con sillas] ), Equipo[Tipo de vuelo] = "Regular" ),
    CALCULATE ( SUM ( Equipo[Sillas] ), Equipo[Tipo de vuelo] = "Regular" )
)"""),
    ("Operación", "Vuelos", "#,0",
     "Número de vuelos (conjunto Tráfico por Equipo).",
     "SUM ( Equipo[Vuelos] )"),
    ("Operación", "Meses con datos", "0",
     "Meses con datos en el periodo filtrado. 2026 tiene 6 (enero a junio): no se compara con años completos.",
     "DISTINCTCOUNT ( Trafico[Fecha] )"),
    ("Rutas", "Pasajeros por aeropuerto", "#,0",
     "Pasajeros que salen más los que llegan. Usa las dos relaciones inactivas con Aeropuertos.",
     """CALCULATE ( [Pasajeros], USERELATIONSHIP ( Trafico[Clave origen], Aeropuertos[Clave] ) )
    + CALCULATE ( [Pasajeros], USERELATIONSHIP ( Trafico[Clave destino], Aeropuertos[Clave] ) )"""),
    ("Rutas", "Pasajeros aeropuertos del mapa", "#,0",
     "Pasajeros (salen + llegan) de los 10 aeropuertos de Colombia con más pasajeros; el resto queda en blanco.",
     """VAR pax = CALCULATE ( [Pasajeros por aeropuerto], KEEPFILTERS ( Aeropuertos[País] = "COLOMBIA" ) )
VAR puesto =
    RANKX (
        ALLSELECTED ( Aeropuertos[Nombre mapa] ),
        CALCULATE ( [Pasajeros por aeropuerto], KEEPFILTERS ( Aeropuertos[País] = "COLOMBIA" ) ),, DESC, DENSE
    )
RETURN
    IF ( NOT ISBLANK ( pax ) && puesto <= 10, pax )"""),
    ("Rutas", "Latitud del mapa", "0.0000",
     "Latitud del aeropuerto, solo si está entre los 10 del mapa (el mapa es un gráfico de dispersión).",
     """IF (
    NOT ISBLANK ( [Pasajeros aeropuertos del mapa] ),
    CALCULATE ( AVERAGE ( Aeropuertos[Latitud] ), KEEPFILTERS ( Aeropuertos[País] = "COLOMBIA" ) )
)"""),
    ("Rutas", "Longitud del mapa", "0.0000",
     "Longitud del aeropuerto, solo si está entre los 10 del mapa.",
     """IF (
    NOT ISBLANK ( [Pasajeros aeropuertos del mapa] ),
    CALCULATE ( AVERAGE ( Aeropuertos[Longitud] ), KEEPFILTERS ( Aeropuertos[País] = "COLOMBIA" ) )
)"""),
    ("Ejes", "Eje top 10 rutas", "#,0",
     "Fin del eje de las barras: 1,15 veces la barra más grande, para que la etiqueta quepa afuera con cualquier año.",
     "1.15 * MAXX ( ALLSELECTED ( Rutas[Nombre ruta] ), [Pasajeros top 10 rutas] )"),
    ("Ejes", "Eje top 10 países", "#,0",
     "Fin del eje de las barras de países: 1,15 veces la barra más grande.",
     "1.15 * MAXX ( ALLSELECTED ( Trafico[País exterior] ), [Pasajeros internacionales top 10 países] )"),
    ("Ejes", "Eje top 10 rutas internacionales", "#,0",
     "Fin del eje de las barras de rutas internacionales: 1,15 veces la barra más grande.",
     "1.15 * MAXX ( ALLSELECTED ( Rutas[Nombre ruta] ), [Pasajeros internacionales top 10 rutas] )"),
    ("Ejes", "Eje carga top 8 rutas", "#,0",
     "Fin del eje de las barras de carga por ruta: 1,15 veces la barra más grande.",
     "1.15 * MAXX ( ALLSELECTED ( Rutas[Nombre ruta] ), [Carga top 8 rutas] )"),
    ("Ejes", "Eje carga top 6 aerolíneas", "#,0",
     "Fin del eje de las barras de carga por aerolínea: 1,15 veces la barra más grande.",
     "1.15 * MAXX ( ALLSELECTED ( Aerolineas[Aerolínea] ), [Carga top 6 aerolíneas] )"),
    ("Rutas", "Pasajeros top 10 rutas", "#,0",
     "Pasajeros solo para las 10 rutas más grandes de lo que esté filtrado; el resto queda en blanco y no se dibuja.",
     """IF (
    RANKX ( ALLSELECTED ( Rutas[Nombre ruta] ), [Pasajeros],, DESC, DENSE ) <= 10,
    [Pasajeros]
)"""),
    ("Rutas", "Pasajeros internacionales top 10 países", "#,0",
     "Pasajeros internacionales de los 10 países con más viajeros.",
     """IF (
    NOT ISBLANK ( [Pasajeros internacionales] )
        && RANKX ( ALLSELECTED ( Trafico[País exterior] ), [Pasajeros internacionales],, DESC, DENSE ) <= 10,
    [Pasajeros internacionales]
)"""),
    ("Rutas", "Pasajeros internacionales top 10 rutas", "#,0",
     "Pasajeros internacionales de las 10 rutas internacionales más grandes.",
     """IF (
    NOT ISBLANK ( [Pasajeros internacionales] )
        && RANKX ( ALLSELECTED ( Rutas[Nombre ruta] ), [Pasajeros internacionales],, DESC, DENSE ) <= 10,
    [Pasajeros internacionales]
)"""),
    ("Temporadas", "Índice de temporada", "0.0",
     "Pasajeros del mes / promedio mensual de su año x 100, promediado de 2022 a 2025. "
     "100 = un mes normal. Ignora el filtro de año: 2020 y 2021 tienen la pandemia y 2026 no está completo.",
     """VAR anios =
    CALCULATETABLE (
        VALUES ( Calendario[Año] ),
        REMOVEFILTERS ( Calendario ),
        Calendario[Año] >= 2022,
        Calendario[Año] <= 2025
    )
VAR indices =
    ADDCOLUMNS (
        anios,
        "@indice",
            VAR a = Calendario[Año]
            VAR delMes = CALCULATE ( [Pasajeros], REMOVEFILTERS ( Calendario[Año], Calendario[Fecha] ), Calendario[Año] = a )
            VAR promedio = CALCULATE ( [Pasajeros], REMOVEFILTERS ( Calendario ), Calendario[Año] = a ) / 12
            RETURN DIVIDE ( delMes, promedio ) * 100
    )
RETURN
    AVERAGEX ( indices, [@indice] )"""),
    ("Temporadas", "Mes más fuerte", None,
     "El mes con el índice de temporada más alto.",
     """VAR meses = ADDCOLUMNS ( SUMMARIZE ( ALL ( Calendario ), Calendario[Mes], Calendario[Mes largo] ), "@i", [Índice de temporada] )
RETURN
    MAXX ( TOPN ( 1, meses, [@i], DESC ), Calendario[Mes largo] )"""),
    ("Temporadas", "Mes más flojo", None,
     "El mes con el índice de temporada más bajo.",
     """VAR meses = ADDCOLUMNS ( SUMMARIZE ( ALL ( Calendario ), Calendario[Mes], Calendario[Mes largo] ), "@i", [Índice de temporada] )
RETURN
    MAXX ( TOPN ( 1, meses, [@i], ASC ), Calendario[Mes largo] )"""),
    ("Carga", "Carga que sale (t)", "#,0",
     "Toneladas en vuelos internacionales que salen de Colombia.",
     'CALCULATE ( [Carga (t)], Trafico[Sentido] = "Sale de Colombia" )'),
    ("Carga", "% carga internacional", "0.0%",
     "Parte de las toneladas que va en vuelos internacionales.",
     """DIVIDE (
    CALCULATE ( [Carga (t)], TipoTrafico[Tráfico] = "Internacional" ),
    CALCULATE ( [Carga (t)], REMOVEFILTERS ( TipoTrafico ) )
)"""),
    ("Carga", "Índice de carga", "0.0",
     "Como el índice de temporada, pero con toneladas. 100 = un mes normal (2022 a 2025).",
     """VAR anios =
    CALCULATETABLE (
        VALUES ( Calendario[Año] ),
        REMOVEFILTERS ( Calendario ),
        Calendario[Año] >= 2022,
        Calendario[Año] <= 2025
    )
VAR indices =
    ADDCOLUMNS (
        anios,
        "@indice",
            VAR a = Calendario[Año]
            VAR delMes = CALCULATE ( [Carga (t)], REMOVEFILTERS ( Calendario[Año], Calendario[Fecha] ), Calendario[Año] = a )
            VAR promedio = CALCULATE ( [Carga (t)], REMOVEFILTERS ( Calendario ), Calendario[Año] = a ) / 12
            RETURN DIVIDE ( delMes, promedio ) * 100
    )
RETURN
    AVERAGEX ( indices, [@indice] )"""),
    ("Carga", "Carga top 8 rutas", "#,0",
     "Toneladas solo para las 8 rutas con más carga.",
     """IF (
    RANKX ( ALLSELECTED ( Rutas[Nombre ruta] ), [Carga (t)],, DESC, DENSE ) <= 8,
    [Carga (t)]
)"""),
    ("Carga", "Carga top 6 aerolíneas", "#,0",
     "Toneladas solo para las 6 aerolíneas con más carga.",
     """IF (
    RANKX ( ALLSELECTED ( Aerolineas[Aerolínea] ), [Carga (t)],, DESC, DENSE ) <= 6,
    [Carga (t)]
)"""),
]


# ---------------------------------------------------------------------------
# Escritura del modelo (TMDL)
# ---------------------------------------------------------------------------
def leer_pq(archivo: str, sin_comentarios: bool = False) -> list[str]:
    lineas = (PQ / archivo).read_text(encoding="utf-8").rstrip().splitlines()
    lineas = [l.rstrip() for l in lineas if l.strip()]
    if sin_comentarios:
        lineas = [l for l in lineas if not l.lstrip().startswith("//")]
    return lineas


def bloque(lineas: list[str], tabs: int) -> str:
    return "\n".join("\t" * tabs + l for l in lineas)


def escribir_modelo() -> None:
    defin = MODELO / "definition"
    (defin / "tables").mkdir(parents=True, exist_ok=True)
    (MODELO / "definition.pbism").write_text(json.dumps({"version": "4.0", "settings": {}}, indent=2), encoding="utf-8")
    (defin / "database.tmdl").write_text("database\n\tcompatibilityLevel: 1600\n", encoding="utf-8")

    orden = [e[0] for e in EXPRESIONES] + list(TABLAS)
    modelo = [
        "model Model",
        "\tculture: es-CO",
        "\tdefaultPowerBIDataSourceVersion: powerBI_V3",
        "\tsourceQueryCulture: es-CO",
        "\tdataAccessOptions",
        "\t\tlegacyRedirects",
        "\t\treturnErrorValuesAsNull",
        "",
        f"annotation PBI_QueryOrder = {json.dumps(orden, ensure_ascii=False)}",
        "",
        "annotation __PBI_TimeIntelligenceEnabled = 0",
        "",
    ] + [f"ref table {q(t)}" for t in list(TABLAS) + ["Medidas"]]
    (defin / "model.tmdl").write_text("\n".join(modelo) + "\n", encoding="utf-8")

    exp = []
    for nombre, archivo, tipo in EXPRESIONES:
        lineas = leer_pq(archivo, sin_comentarios=(tipo == "Text"))
        if len(lineas) == 1:
            exp.append(f"expression {q(nombre)} = {lineas[0]}")
        else:
            exp.append(f"expression {q(nombre)} =")
            exp.append(bloque(lineas, 2))
        exp += [f"\tlineageTag: {tag('exp', nombre)}", "", f"\tannotation PBI_ResultType = {tipo}", ""]
    (defin / "expressions.tmdl").write_text("\n".join(exp), encoding="utf-8")

    for tabla, (archivo, columnas) in TABLAS.items():
        out = [f"table {q(tabla)}", f"\tlineageTag: {tag('t', tabla)}", ""]
        for nombre, tipo, formato, resumen, oculta, extra in columnas:
            out.append(f"\tcolumn {q(nombre)}")
            out.append(f"\t\tdataType: {tipo}")
            if formato:
                out.append(f"\t\tformatString: {formato}")
            if oculta:
                out.append("\t\tisHidden")
            if "dataCategory" in extra:
                out.append(f"\t\tdataCategory: {extra['dataCategory']}")
            out.append(f"\t\tlineageTag: {tag('c', tabla, nombre)}")
            out.append(f"\t\tsummarizeBy: {resumen}")
            out.append(f"\t\tsourceColumn: {nombre}")
            if "sortByColumn" in extra:
                out.append(f"\t\tsortByColumn: {q(extra['sortByColumn'])}")
            out += ["", "\t\tannotation SummarizationSetBy = User", ""]
        out.append(f"\tpartition {q(tabla)} = m")
        out.append("\t\tmode: import")
        lineas = leer_pq(archivo)
        if len(lineas) == 1:
            out.append(f"\t\tsource = {lineas[0]}")
        else:
            out.append("\t\tsource =")
            out.append(bloque(lineas, 4))
        out += ["", "\tannotation PBI_ResultType = Table", ""]
        (defin / "tables" / f"{tabla}.tmdl").write_text("\n".join(out), encoding="utf-8")

    # Tabla de medidas: una columna oculta y todas las medidas
    out = ["table Medidas", f"\tlineageTag: {tag('t', 'Medidas')}", ""]
    for carpeta, nombre, formato, descripcion, expresion in MEDIDAS:
        lineas = expresion.splitlines()
        for d in descripcion.splitlines():
            out.append(f"\t/// {d}")
        if len(lineas) == 1:
            out.append(f"\tmeasure {q(nombre)} = {lineas[0]}")
        else:
            out.append(f"\tmeasure {q(nombre)} =")
            out.append(bloque(lineas, 3))
        if formato:
            out.append(f"\t\tformatString: {formato}")
        out.append(f"\t\tdisplayFolder: {carpeta}")
        out.append(f"\t\tlineageTag: {tag('m', nombre)}")
        out.append("")
    out += [
        "\tcolumn Columna",
        "\t\tdataType: string",
        "\t\tisHidden",
        f"\t\tlineageTag: {tag('c', 'Medidas', 'Columna')}",
        "\t\tsummarizeBy: none",
        "\t\tsourceColumn: Columna",
        "",
        "\tpartition Medidas = m",
        "\t\tmode: import",
        "\t\tsource = #table(type table [Columna = text], {})",
        "",
        "\tannotation PBI_ResultType = Table",
        "",
    ]
    (defin / "tables" / "Medidas.tmdl").write_text("\n".join(out), encoding="utf-8")

    rel = []
    for desde, hacia, activa in RELACIONES:
        t1, c1 = desde.split(".", 1)
        t2, c2 = hacia.split(".", 1)
        rel.append(f"relationship {tag('r', desde, hacia)}")
        if not activa:
            rel.append("\tisActive: false")
        rel.append(f"\tfromColumn: {q(t1)}.{q(c1)}")
        rel.append(f"\ttoColumn: {q(t2)}.{q(c2)}")
        rel.append("")
    (defin / "relationships.tmdl").write_text("\n".join(rel), encoding="utf-8")


# ---------------------------------------------------------------------------
# Informe (PBIR): ayudas para armar visuales
# ---------------------------------------------------------------------------
def lit(valor) -> dict:
    if isinstance(valor, bool):
        v = "true" if valor else "false"
    elif isinstance(valor, (int, float)):
        v = f"{valor}D"
    else:
        v = "'" + str(valor).replace("'", "''") + "'"
    return {"expr": {"Literal": {"Value": v}}}


def color(hex_: str) -> dict:
    return {"solid": {"color": lit(hex_)}}


def col(tabla: str, columna: str) -> dict:
    return {"Column": {"Expression": {"SourceRef": {"Entity": tabla}}, "Property": columna}}


def med(nombre: str) -> dict:
    return {"Measure": {"Expression": {"SourceRef": {"Entity": "Medidas"}}, "Property": nombre}}



def proyeccion(campo: dict, nombre: str | None = None) -> dict:
    if "Measure" in campo:
        ref = f"Medidas.{campo['Measure']['Property']}"
        nativo = campo["Measure"]["Property"]
    elif "Column" in campo:
        ref = f"{campo['Column']['Expression']['SourceRef']['Entity']}.{campo['Column']['Property']}"
        nativo = campo["Column"]["Property"]
    else:
        c = campo["Aggregation"]["Expression"]["Column"]
        ref = f"Avg({c['Expression']['SourceRef']['Entity']}.{c['Property']})"
        nativo = f"Promedio de {c['Property']}"
    p = {"field": campo, "queryRef": ref, "nativeQueryRef": nativo}
    if nombre:
        p["displayName"] = nombre
    return p


def titulo(texto: str, tamano: int = 11) -> dict:
    return {
        "title": [{"properties": {"show": lit(True), "text": lit(texto), "fontColor": color(TEXTO),
                                  "fontSize": lit(tamano), "fontFamily": lit("Segoe UI Semibold"),
                                  "alignment": lit("left")}}],
        "border": [{"properties": {"show": lit(True), "color": color(BORDE), "radius": lit(2)}}],
        "background": [{"properties": {"show": lit(True), "color": color("#ffffff"), "transparency": lit(0)}}],
        "dropShadow": [{"properties": {"show": lit(False)}}],
        "padding": [{"properties": {"top": lit(8), "bottom": lit(8), "left": lit(12), "right": lit(12)}}],
    }


class Pagina:
    def __init__(self, nombre: str, mostrar: str):
        self.nombre, self.mostrar, self.visuales = nombre, mostrar, []
        self.interacciones = []

    def sin_filtro(self, origen: str, *destinos: str):
        """El segmentador `origen` no filtra estos visuales (por ejemplo, gráficas que muestran todos los años)."""
        self.interacciones += [{"source": origen, "target": d, "type": "NoFilter"} for d in destinos]

    def agregar(self, nombre: str, x, y, w, h, visual: dict, contenedor: dict | None = None):
        assert x + w <= 1280 and y + h <= 720, (self.nombre, nombre)
        v = {
            "$schema": f"{SCHEMA}/visualContainer/2.4.0/schema.json",
            "name": nombre,
            "position": {"x": x, "y": y, "z": len(self.visuales) * 1000, "width": w, "height": h,
                         "tabOrder": len(self.visuales) * 1000},
            "visual": visual,
        }
        if contenedor is not None:
            v["visual"]["visualContainerObjects"] = contenedor
        self.visuales.append(v)

    # --- tipos de visual -------------------------------------------------
    def texto(self, nombre, x, y, w, h, titulo_txt: str, subtitulo: str):
        parrafos = [
            {"textRuns": [{"value": titulo_txt, "textStyle": {"fontFamily": "Segoe UI Semibold", "fontSize": "18pt",
                                                              "color": TEXTO}}]},
            {"textRuns": [{"value": subtitulo, "textStyle": {"fontFamily": "Segoe UI", "fontSize": "10pt",
                                                             "color": GRIS}}]},
        ]
        self.agregar(nombre, x, y, w, h, {"visualType": "textbox",
                                          "objects": {"general": [{"properties": {"paragraphs": parrafos}}]}},
                     {"background": [{"properties": {"show": lit(False)}}],
                      "border": [{"properties": {"show": lit(False)}}]})

    def segmentador(self, nombre, x, y, w, h, campo: dict, etiqueta: str, valor_inicial=None):
        objetos = {"data": [{"properties": {"mode": lit("Dropdown")}}],
                   "header": [{"properties": {"show": lit(True), "text": lit(etiqueta), "fontColor": color(GRIS),
                                              "textSize": lit(9)}}]}
        if valor_inicial is not None:
            t, c = campo["Column"]["Expression"]["SourceRef"]["Entity"], campo["Column"]["Property"]
            valor = f"{valor_inicial}L" if isinstance(valor_inicial, int) else f"'{valor_inicial}'"
            objetos["general"] = [{"properties": {"filter": {"filter": {
                "Version": 2,
                "From": [{"Name": "s", "Entity": t, "Type": 0}],
                "Where": [{"Condition": {"In": {
                    "Expressions": [{"Column": {"Expression": {"SourceRef": {"Source": "s"}}, "Property": c}}],
                    "Values": [[{"Literal": {"Value": valor}}]]}}}]}}}}]
        visual = {"visualType": "slicer",
                  "query": {"queryState": {"Values": {"projections": [proyeccion(campo)]}}},
                  "objects": objetos,
                  "syncGroup": {"groupName": etiqueta, "fieldChanges": True, "filterChanges": True}}
        self.agregar(nombre, x, y, w, h, visual, {"border": [{"properties": {"show": lit(False)}}],
                                                  "background": [{"properties": {"show": lit(False)}}]})

    def tarjeta(self, nombre, x, y, w, h, medida: str, etiqueta: str, unidades: int = 0):
        visual = {"visualType": "card",
                  "query": {"queryState": {"Values": {"projections": [proyeccion(med(medida), etiqueta)]}}},
                  "objects": {
                      "labels": [{"properties": {"color": color(ACENTO), "fontSize": lit(24),
                                                 "fontFamily": lit("Segoe UI Semibold"),
                                                 "labelDisplayUnits": lit(unidades)}}],
                      "categoryLabels": [{"properties": {"show": lit(True), "color": color(GRIS),
                                                         "fontSize": lit(10)}}]}}
        contenedor = titulo("")
        contenedor["title"][0]["properties"]["show"] = lit(False)
        self.agregar(nombre, x, y, w, h, visual, contenedor)

    def grafica(self, nombre, x, y, w, h, tipo: str, roles: dict, titulo_txt: str,
                orden: dict | None = None, objetos: dict | None = None):
        estado = {rol: {"projections": [proyeccion(c, n) for c, n in campos]} for rol, campos in roles.items()}
        visual = {"visualType": tipo, "query": {"queryState": estado}}
        if orden:
            visual["query"]["sortDefinition"] = {"sort": [{"field": orden["campo"], "direction": orden["dir"]}],
                                                 "isDefaultSort": False}
        base = {
            "categoryAxis": [{"properties": {"labelColor": color(GRIS), "fontSize": lit(9),
                                             "showAxisTitle": lit(False)}}],
            "valueAxis": [{"properties": {"labelColor": color(GRIS), "fontSize": lit(9),
                                          "showAxisTitle": lit(False), "gridlineColor": color("#eceef0")}}],
            "legend": [{"properties": {"show": lit(len(roles.get("Series", [])) > 0 or len(roles.get("Y", [])) > 1),
                                       "position": lit("Top"), "labelColor": color(GRIS), "fontSize": lit(9)}}],
        }
        if tipo == "clusteredBarChart":
            base["valueAxis"] = [{"properties": {"show": lit(False), "gridlineShow": lit(False)}}]
            base["categoryAxis"][0]["properties"]["maxMarginFactor"] = lit(45)
        if objetos:
            base.update(objetos)
        if tipo in ("tableEx", "azureMap", "scatterChart"):
            base = objetos or {}
        visual["objects"] = base
        self.agregar(nombre, x, y, w, h, visual, titulo(titulo_txt))


def color_serie(hex_: str) -> dict:
    return {"dataPoint": [{"properties": {"fill": color(hex_)}}]}


def color_por_valor(campo: dict, valor: str, hex_: str) -> dict:
    """Color fijo para una serie (por ejemplo, el sentido "Sale de Colombia" con el color de acento)."""
    return {"properties": {"fill": color(hex_)},
            "selector": {"data": [{"scopeId": {"Comparison": {
                "ComparisonKind": 0, "Left": campo, "Right": {"Literal": {"Value": f"'{valor}'"}}}}}]}}


def etiquetas(mostrar=True, unidades=0) -> dict:
    return {"labels": [{"properties": {"show": lit(mostrar), "color": color(TEXTO), "fontSize": lit(9),
                                       "labelDisplayUnits": lit(unidades)}}]}


def barras(eje: str, unidades=0) -> dict:
    """Barras horizontales: color de acento, etiqueta siempre afuera y el eje hasta 1,15 veces la barra más
    grande (medida `eje`), para que la etiqueta de la barra más larga no quede adentro con ningún año."""
    o = {**color_serie(ACENTO), **etiquetas(True, unidades)}
    o["labels"][0]["properties"]["labelPosition"] = lit("OutsideEnd")
    o["valueAxis"] = [{"properties": {"show": lit(False), "gridlineShow": lit(False),
                                      "start": lit(0), "end": {"expr": med(eje)}}}]
    return o


# ---------------------------------------------------------------------------
# Las paginas
# ---------------------------------------------------------------------------
FUENTE = "Fuente: Aerocivil en datos.gov.co, licencia CC BY-SA 4.0. Cifras de 2022 a 2025 provisionales; 2026 llega a junio."
ANIO = col("Calendario", "Año")
TRAF = col("TipoTrafico", "Tráfico")


def encabezado(p: Pagina, titulo_txt: str, subtitulo: str, anio=True, trafico=True):
    p.texto("titulo", 24, 12, 820, 64, titulo_txt, subtitulo)
    x = 1256
    if trafico:
        x -= 170
        p.segmentador("filtroTrafico", x, 18, 170, 56, TRAF, "Tráfico")
    if anio:
        x -= 186
        p.segmentador("filtroAnio", x, 18, 170, 56, ANIO, "Año", 2025)


def paginas() -> list[Pagina]:
    ps = []

    # 1. Resumen y rutas ---------------------------------------------------
    p = Pagina("p1_resumen", "Resumen y rutas")
    encabezado(p, "Vuelos en Colombia: ¿qué rutas mueven más pasajeros?", FUENTE)
    w = (1232 - 3 * 16) // 4
    p.tarjeta("kpiPasajeros", 24, 92, w, 92, "Pasajeros", "Pasajeros")
    p.tarjeta("kpiVariacion", 24 + (w + 16), 92, w, 92, "Variación vs año anterior", "Pasajeros vs mismos meses del año anterior")
    p.tarjeta("kpiCarga", 24 + 2 * (w + 16), 92, w, 92, "Carga (t)", "Carga y correo (toneladas)")
    p.tarjeta("kpiOcupacion", 24 + 3 * (w + 16), 92, w, 92, "Ocupación", "Ocupación del tráfico elegido")
    # Mapa sin Azure Maps (pide iniciar sesión): dispersión con longitud y latitud, sin ejes
    sin_eje = [{"properties": {"show": lit(False), "gridlineShow": lit(False), "showAxisTitle": lit(False)}}]
    p.grafica("mapaAeropuertos", 24, 200, 560, 496, "scatterChart",
              {"Category": [(col("Aeropuertos", "Nombre mapa"), "Aeropuerto")],
               "X": [(med("Longitud del mapa"), "Longitud")],
               "Y": [(med("Latitud del mapa"), "Latitud")],
               "Size": [(med("Pasajeros aeropuertos del mapa"), "Pasajeros")]},
              "Los 10 aeropuertos con más pasajeros (San Andrés queda fuera del recuadro)",
              # recuadro fijo en Colombia continental: San Andres (muy al oeste) apretaba todo y los nombres se cruzaban
              objetos={"categoryAxis": [{"properties": {**sin_eje[0]["properties"], "start": lit(-77.3), "end": lit(-71.7)}}],
                       "valueAxis": [{"properties": {**sin_eje[0]["properties"], "start": lit(2.8), "end": lit(11.9)}}],
                       "categoryLabels": [{"properties": {"show": lit(True), "color": color(TEXTO),
                                                          "fontSize": lit(9)}}],
                       "bubbles": [{"properties": {"bubbleSize": lit(-12)}}],
                       **color_serie(ACENTO)})
    p.grafica("topRutas", 600, 200, 656, 496, "clusteredBarChart",
              {"Category": [(col("Rutas", "Nombre ruta"), "Ruta")],
               "Y": [(med("Pasajeros top 10 rutas"), "Pasajeros")]},
              "Las 10 rutas con más pasajeros (ida y vuelta)",
              orden={"campo": med("Pasajeros top 10 rutas"), "dir": "Descending"},
              objetos=barras("Eje top 10 rutas"))
    ps.append(p)

    # 2. Temporadas ----------------------------------------------------------
    p = Pagina("p2_temporadas", "Temporadas")
    encabezado(p, "Temporadas: ¿en qué meses se vuela más?",
               "Índice de temporada: 100 = un mes normal. Promedio de 2022 a 2025 (2020 y 2021 tienen la pandemia).",
               anio=False)
    p.grafica("indiceMes", 24, 92, 880, 380, "lineChart",
              {"Category": [(col("Calendario", "Nombre mes"), "Mes")],
               "Y": [(med("Índice de temporada"), "Índice")],
               "Series": [(TRAF, "Tráfico")]},
              "Índice de temporada por mes",
              orden={"campo": col("Calendario", "Nombre mes"), "dir": "Ascending"},
              objetos={"labels": [{"properties": {"show": lit(True), "fontSize": lit(8), "color": color(GRIS)}}]})
    p.tarjeta("kpiMesFuerte", 920, 92, 336, 182, "Mes más fuerte", "Mes más fuerte")
    p.tarjeta("kpiMesFlojo", 920, 290, 336, 182, "Mes más flojo", "Mes más flojo")
    p.grafica("pasajerosMes", 24, 488, 1232, 208, "lineChart",
              {"Category": [(col("Calendario", "Fecha"), "Mes")],
               "Y": [(med("Pasajeros"), "Pasajeros")],
               "Series": [(TRAF, "Tráfico")]},
              "Pasajeros por mes, enero de 2020 a junio de 2026")
    ps.append(p)

    # 3. Aerolineas ----------------------------------------------------------
    p = Pagina("p3_aerolineas", "Aerolíneas")
    encabezado(p, "Aerolíneas: ¿quién mueve a los pasajeros nacionales?",
               "Viva Air reporta vuelos hasta febrero de 2023 y Ultra Air hasta marzo de 2023. "
               "HHI de más de 2.500 = mercado muy concentrado.",
               trafico=False)
    p.grafica("participacion", 24, 92, 760, 400, "hundredPercentStackedColumnChart",
              {"Category": [(ANIO, "Año")],
               "Y": [(med("Pasajeros nacionales"), "Pasajeros nacionales")],
               "Series": [(col("Aerolineas", "Grupo tablero"), "Grupo")]},
              "Participación en los pasajeros nacionales, por año",
              orden={"campo": ANIO, "dir": "Ascending"})
    p.grafica("hhi", 800, 92, 456, 400, "lineChart",
              {"Category": [(ANIO, "Año")], "Y": [(med("HHI nacional"), "HHI")]},
              "Concentración del mercado nacional (HHI)",
              orden={"campo": ANIO, "dir": "Ascending"},
              objetos={**color_serie(ACENTO), **etiquetas(True, 0)})
    p.grafica("tablaAerolineas", 24, 508, 1232, 188, "tableEx",
              {"Values": [(col("Aerolineas", "Aerolínea"), "Aerolínea"),
                          (col("Aerolineas", "Grupo empresarial"), "Grupo"),
                          (med("Pasajeros nacionales"), "Pasajeros nacionales"),
                          (med("Participación nacional"), "Participación"),
                          (med("Ocupación"), "Ocupación")]},
              "Aerolíneas en el año elegido",
              orden={"campo": med("Pasajeros nacionales"), "dir": "Descending"})
    p.sin_filtro("filtroAnio", "participacion", "hhi")
    ps.append(p)

    # 4. Nacional e internacional -------------------------------------------
    p = Pagina("p4_nacional_internacional", "Nacional e internacional")
    encabezado(p, "Nacional e internacional: ¿dónde está el crecimiento?",
               "Las barras muestran todos los años; los dos gráficos de abajo, el año elegido.", trafico=False)
    p.grafica("paxAnio", 24, 92, 760, 268, "columnChart",
              {"Category": [(ANIO, "Año")],
               "Y": [(med("Pasajeros nacionales"), "Nacionales"), (med("Pasajeros internacionales"), "Internacionales")]},
              "Pasajeros por año (2026: enero a junio)",
              orden={"campo": ANIO, "dir": "Ascending"})
    p.grafica("pctInternacional", 800, 92, 456, 268, "lineChart",
              {"Category": [(ANIO, "Año")], "Y": [(med("% internacional"), "% internacional")]},
              "Parte internacional de los pasajeros",
              orden={"campo": ANIO, "dir": "Ascending"},
              objetos={**color_serie(ACENTO), **etiquetas(True, 0)})
    p.grafica("topPaises", 24, 376, 608, 320, "clusteredBarChart",
              {"Category": [(col("Trafico", "País exterior"), "País")],
               "Y": [(med("Pasajeros internacionales top 10 países"), "Pasajeros")]},
              "Los 10 países con más viajeros",
              orden={"campo": med("Pasajeros internacionales top 10 países"), "dir": "Descending"},
              objetos=barras("Eje top 10 países"))
    p.grafica("topRutasInt", 648, 376, 608, 320, "clusteredBarChart",
              {"Category": [(col("Rutas", "Nombre ruta"), "Ruta")],
               "Y": [(med("Pasajeros internacionales top 10 rutas"), "Pasajeros")]},
              "Las 10 rutas internacionales más grandes",
              orden={"campo": med("Pasajeros internacionales top 10 rutas"), "dir": "Descending"},
              objetos=barras("Eje top 10 rutas internacionales"))
    p.sin_filtro("filtroAnio", "paxAnio", "pctInternacional")
    ps.append(p)

    # 5. Carga ---------------------------------------------------------------
    p = Pagina("p5_carga", "Carga")
    encabezado(p, "Carga: ¿por dónde y cuándo se mueve?",
               "Carga más correo en toneladas. El índice usa 2022 a 2025 (100 = mes normal).", trafico=False)
    w = (1232 - 2 * 16) // 3
    p.tarjeta("kpiCargaT", 24, 92, w, 76, "Carga (t)", "Carga y correo (toneladas)")
    p.tarjeta("kpiCargaInt", 24 + (w + 16), 92, w, 76, "% carga internacional", "En vuelos internacionales")
    p.tarjeta("kpiCargaSale", 24 + 2 * (w + 16), 92, w, 76, "Carga que sale (t)", "Sale de Colombia (toneladas)")
    p.grafica("indiceCarga", 24, 184, 608, 512, "lineChart",
              {"Category": [(col("Calendario", "Nombre mes"), "Mes")],
               "Y": [(med("Índice de carga"), "Índice")],
               "Series": [(col("Trafico", "Sentido"), "Sentido")]},
              "Índice de carga por mes y sentido",
              orden={"campo": col("Calendario", "Nombre mes"), "dir": "Ascending"},
              objetos={"dataPoint": [color_por_valor(col("Trafico", "Sentido"), "Sale de Colombia", ACENTO),
                                     color_por_valor(col("Trafico", "Sentido"), "Entra a Colombia", "#a3acb2"),
                                     color_por_valor(col("Trafico", "Sentido"), "Nacional", "#d0d6d9")]})
    p.grafica("topRutasCarga", 648, 184, 608, 276, "clusteredBarChart",
              {"Category": [(col("Rutas", "Nombre ruta"), "Ruta")],
               "Y": [(med("Carga top 8 rutas"), "Toneladas")]},
              "Las 8 rutas con más carga (toneladas)",
              orden={"campo": med("Carga top 8 rutas"), "dir": "Descending"},
              objetos=barras("Eje carga top 8 rutas", 1))
    p.grafica("topAerolineasCarga", 648, 476, 608, 220, "clusteredBarChart",
              {"Category": [(col("Aerolineas", "Aerolínea"), "Aerolínea")],
               "Y": [(med("Carga top 6 aerolíneas"), "Toneladas")]},
              "Las 6 aerolíneas con más carga (toneladas)",
              orden={"campo": med("Carga top 6 aerolíneas"), "dir": "Descending"},
              objetos=barras("Eje carga top 6 aerolíneas", 1))
    ps.append(p)

    # 6. Control de datos ----------------------------------------------------
    p = Pagina("p6_control", "Control de datos")
    p.texto("titulo", 24, 12, 1232, 64, "Control: totales por año",
            "Para comparar contra resultados/10_resumen_anual.csv (SQL): deben dar exactamente lo mismo. "
            "Aquí la ocupación junta nacional e internacional; resultados/16_ocupacion.csv la separa.")
    p.grafica("tablaControl", 24, 92, 1232, 320, "tableEx",
              {"Values": [(ANIO, "Año"), (med("Meses con datos"), "Meses"), (med("Pasajeros"), "Pasajeros"),
                          (med("Pasajeros nacionales"), "Nacionales"),
                          (med("Pasajeros internacionales"), "Internacionales"),
                          (med("Carga (t)"), "Carga (t)"), (med("Ocupación"), "Ocupación"),
                          (med("Vuelos"), "Vuelos")]},
              "Totales por año (sin filtros)",
              orden={"campo": ANIO, "dir": "Ascending"})
    ps.append(p)
    return ps


TEMA = {
    "name": "Vuelos Colombia sobrio",
    "dataColors": [ACENTO, "#8aa597", "#5b6770", "#c3cfc8", "#a3acb2", "#3f7a5e", "#d9dee1", "#73867c",
                   "#404850", "#b0bdb5"],
    "background": "#ffffff",
    "foreground": TEXTO,
    "tableAccent": ACENTO,
    "textClasses": {
        "callout": {"fontSize": 24, "fontFace": "Segoe UI Semibold", "color": ACENTO},
        "title": {"fontSize": 11, "fontFace": "Segoe UI Semibold", "color": TEXTO},
        "header": {"fontSize": 10, "fontFace": "Segoe UI Semibold", "color": TEXTO},
        "label": {"fontSize": 9, "fontFace": "Segoe UI", "color": GRIS},
    },
    "visualStyles": {
        "page": {"*": {"background": [{"color": {"solid": {"color": FONDO_PAGINA}}, "transparency": 0}],
                       "outspace": [{"color": {"solid": {"color": FONDO_PAGINA}}}]}},
        "*": {"*": {"dropShadow": [{"show": False}],
                    "border": [{"show": True, "color": {"solid": {"color": BORDE}}, "radius": 2}]}},
    },
}


def escribir_informe() -> None:
    defin = INFORME / "definition"
    INFORME.mkdir(parents=True, exist_ok=True)
    (INFORME / "definition.pbir").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {"byPath": {"path": f"../{NOMBRE}.SemanticModel"}},
    }, indent=2), encoding="utf-8")
    defin.mkdir(parents=True, exist_ok=True)
    (defin / "version.json").write_text(json.dumps({
        "$schema": f"{SCHEMA}/versionMetadata/1.0.0/schema.json", "version": "2.0.0"}, indent=2), encoding="utf-8")
    recursos = INFORME / "StaticResources" / "RegisteredResources"
    recursos.mkdir(parents=True, exist_ok=True)
    (recursos / "tema_vuelos.json").write_text(json.dumps(TEMA, indent=2, ensure_ascii=False), encoding="utf-8")
    version_tema = {"visual": "2.4.0", "report": "3.0.0", "page": "2.0.0"}
    (defin / "report.json").write_text(json.dumps({
        "$schema": f"{SCHEMA}/report/3.0.0/schema.json",
        "themeCollection": {"customTheme": {"name": "tema_vuelos.json", "reportVersionAtImport": version_tema,
                                            "type": "RegisteredResources"}},
        "resourcePackages": [{"name": "RegisteredResources", "type": "RegisteredResources",
                              "items": [{"name": "tema_vuelos.json", "path": "tema_vuelos.json",
                                         "type": "CustomTheme"}]}],
        "settings": {"useStylableVisualContainerHeader": True, "exportDataMode": "AllowSummarized",
                     "defaultDrillFilterOtherVisuals": True, "allowChangeFilterTypes": True},
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    ps = paginas()
    carpeta_paginas = defin / "pages"
    carpeta_paginas.mkdir(exist_ok=True)
    (carpeta_paginas / "pages.json").write_text(json.dumps({
        "$schema": f"{SCHEMA}/pagesMetadata/1.0.0/schema.json",
        "pageOrder": [p.nombre for p in ps], "activePageName": ps[0].nombre}, indent=2), encoding="utf-8")
    for p in ps:
        cp = carpeta_paginas / p.nombre
        (cp / "visuals").mkdir(parents=True, exist_ok=True)
        (cp / "page.json").write_text(json.dumps({
            "$schema": f"{SCHEMA}/page/2.0.0/schema.json", "name": p.nombre, "displayName": p.mostrar,
            "displayOption": "FitToPage", "height": 720, "width": 1280,
            **({"visualInteractions": p.interacciones} if p.interacciones else {})}, indent=2, ensure_ascii=False),
            encoding="utf-8")
        for v in p.visuales:
            cv = cp / "visuals" / v["name"]
            cv.mkdir(parents=True, exist_ok=True)
            (cv / "visual.json").write_text(json.dumps(v, indent=2, ensure_ascii=False), encoding="utf-8")

    (SALIDA / f"{NOMBRE}.pbip").write_text(json.dumps({
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [{"report": {"path": f"{NOMBRE}.Report"}}],
        "settings": {"enableAutoRecovery": True}}, indent=2), encoding="utf-8")


def escribir_medidas_md() -> None:
    out = [
        "# Medidas DAX del tablero",
        "",
        "Todas viven en la tabla `Medidas` de `powerbi/vuelos-colombia.pbip`. Este archivo lo escribe",
        "`powerbi/generar_tablero.py`, así que siempre coincide con el tablero.",
        "",
        "Tablas del modelo (estrella): `Trafico` y `Equipo` son los hechos; `Calendario`, `Rutas`, `Aerolineas`,",
        "`TipoTrafico` y `Aeropuertos` las dimensiones. `Aeropuertos` se une a `Trafico` dos veces (origen y",
        "destino) con relaciones inactivas que se encienden con `USERELATIONSHIP`.",
        "",
    ]
    carpeta = None
    for c, nombre, formato, descripcion, expresion in MEDIDAS:
        if c != carpeta:
            out += [f"## {c}", ""]
            carpeta = c
        out += [f"### {nombre}", "", descripcion, ""]
        if formato:
            out += [f"Formato: `{formato}`", ""]
        out += ["```dax", f"{nombre} =", expresion, "```", ""]
    (RAIZ / "dax").mkdir(exist_ok=True)
    (RAIZ / "dax" / "medidas.md").write_text("\n".join(out), encoding="utf-8")


def main() -> None:
    for carpeta in (MODELO / "definition", INFORME / "definition", INFORME / "StaticResources"):
        if carpeta.exists():
            shutil.rmtree(carpeta)
    escribir_modelo()
    escribir_informe()
    escribir_medidas_md()
    n = sum(len(p.visuales) for p in paginas())
    print(f"Listo: {NOMBRE}.pbip con {len(TABLAS) + 1} tablas, {len(MEDIDAS)} medidas, "
          f"{len(paginas())} páginas y {n} visuales. dax/medidas.md al día.")


if __name__ == "__main__":
    main()
