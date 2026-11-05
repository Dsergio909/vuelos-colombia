# Medidas DAX del tablero

Todas viven en la tabla `Medidas` de `powerbi/vuelos-colombia.pbip`. Este archivo lo escribe
`powerbi/generar_tablero.py`, así que siempre coincide con el tablero.

Tablas del modelo (estrella): `Trafico` y `Equipo` son los hechos; `Calendario`, `Rutas`, `Aerolineas`,
`TipoTrafico` y `Aeropuertos` las dimensiones. `Aeropuertos` se une a `Trafico` dos veces (origen y
destino) con relaciones inactivas que se encienden con `USERELATIONSHIP`.

## Base

### Pasajeros

Pasajeros de pago (dato de Aerocivil, conjunto Origen-Destino).

Formato: `#,0`

```dax
Pasajeros =
SUM ( Trafico[Pasajeros] )
```

### Carga (t)

Carga más correo, en toneladas.

Formato: `#,0`

```dax
Carga (t) =
DIVIDE ( SUM ( Trafico[Carga kg] ), 1000 )
```

### Pasajeros nacionales

Pasajeros de vuelos nacionales. Ignora el filtro de tráfico a propósito.

Formato: `#,0`

```dax
Pasajeros nacionales =
CALCULATE ( [Pasajeros], TipoTrafico[Tráfico] = "Nacional" )
```

### Pasajeros internacionales

Pasajeros de vuelos internacionales (salen o llegan a Colombia).

Formato: `#,0`

```dax
Pasajeros internacionales =
CALCULATE ( [Pasajeros], TipoTrafico[Tráfico] = "Internacional" )
```

### % internacional

Parte de los pasajeros que vuela fuera del país.

Formato: `0.0%`

```dax
% internacional =
DIVIDE ( [Pasajeros internacionales], [Pasajeros nacionales] + [Pasajeros internacionales] )
```

## Comparación

### Pasajeros año anterior

Los mismos meses del año anterior. Si se ve 2026 (enero a junio), compara contra enero a junio de 2025.

Formato: `#,0`

```dax
Pasajeros año anterior =
VAR anio = MAX ( Calendario[Año] )
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
    )
```

### Variación vs año anterior

Cambio de pasajeros contra los mismos meses del año anterior.

Formato: `+0.0%;-0.0%;0.0%`

```dax
Variación vs año anterior =
DIVIDE ( [Pasajeros] - [Pasajeros año anterior], [Pasajeros año anterior] )
```

## Aerolíneas

### Participación nacional

Parte de los pasajeros nacionales que lleva cada aerolínea o grupo.

Formato: `0.0%`

```dax
Participación nacional =
DIVIDE ( [Pasajeros nacionales], CALCULATE ( [Pasajeros nacionales], REMOVEFILTERS ( Aerolineas ) ) )
```

### HHI nacional

Índice de Herfindahl-Hirschman: suma de las participaciones al cuadrado (de 0 a 10.000). Más de 2.500 es un mercado muy concentrado. Se calcula por grupo empresarial.

Formato: `#,0`

```dax
HHI nacional =
SUMX (
    VALUES ( Aerolineas[Grupo empresarial] ),
    VAR s =
        100
            * DIVIDE (
                CALCULATE ( [Pasajeros nacionales] ),
                CALCULATE ( [Pasajeros nacionales], REMOVEFILTERS ( Aerolineas ) )
            )
    RETURN
        s * s
)
```

## Operación

### Ocupación

Pasajeros a bordo / sillas ofrecidas, en vuelos regulares con sillas reportadas (conjunto Tráfico por Equipo).

Formato: `0.0%`

```dax
Ocupación =
DIVIDE (
    CALCULATE ( SUM ( Equipo[Pasajeros con sillas] ), Equipo[Tipo de vuelo] = "Regular" ),
    CALCULATE ( SUM ( Equipo[Sillas] ), Equipo[Tipo de vuelo] = "Regular" )
)
```

### Vuelos

Número de vuelos (conjunto Tráfico por Equipo).

Formato: `#,0`

```dax
Vuelos =
SUM ( Equipo[Vuelos] )
```

### Meses con datos

Meses con datos en el periodo filtrado. 2026 tiene 6 (enero a junio): no se compara con años completos.

Formato: `0`

```dax
Meses con datos =
DISTINCTCOUNT ( Trafico[Fecha] )
```

## Rutas

### Pasajeros por aeropuerto

Pasajeros que salen más los que llegan. Usa las dos relaciones inactivas con Aeropuertos.

Formato: `#,0`

```dax
Pasajeros por aeropuerto =
CALCULATE ( [Pasajeros], USERELATIONSHIP ( Trafico[Clave origen], Aeropuertos[Clave] ) )
    + CALCULATE ( [Pasajeros], USERELATIONSHIP ( Trafico[Clave destino], Aeropuertos[Clave] ) )
```

### Pasajeros aeropuertos del mapa

Pasajeros (salen + llegan) de los 10 aeropuertos de Colombia con más pasajeros; el resto queda en blanco.

Formato: `#,0`

```dax
Pasajeros aeropuertos del mapa =
VAR pax = CALCULATE ( [Pasajeros por aeropuerto], KEEPFILTERS ( Aeropuertos[País] = "COLOMBIA" ) )
VAR puesto =
    RANKX (
        ALLSELECTED ( Aeropuertos[Ciudad aeropuerto] ),
        CALCULATE ( [Pasajeros por aeropuerto], KEEPFILTERS ( Aeropuertos[País] = "COLOMBIA" ) ),, DESC, DENSE
    )
RETURN
    IF ( NOT ISBLANK ( pax ) && puesto <= 10, pax )
```

### Latitud del mapa

Latitud del aeropuerto, solo si está entre los 10 del mapa (el mapa es un gráfico de dispersión).

Formato: `0.0000`

```dax
Latitud del mapa =
IF (
    NOT ISBLANK ( [Pasajeros aeropuertos del mapa] ),
    CALCULATE ( AVERAGE ( Aeropuertos[Latitud] ), KEEPFILTERS ( Aeropuertos[País] = "COLOMBIA" ) )
)
```

### Longitud del mapa

Longitud del aeropuerto, solo si está entre los 10 del mapa.

Formato: `0.0000`

```dax
Longitud del mapa =
IF (
    NOT ISBLANK ( [Pasajeros aeropuertos del mapa] ),
    CALCULATE ( AVERAGE ( Aeropuertos[Longitud] ), KEEPFILTERS ( Aeropuertos[País] = "COLOMBIA" ) )
)
```

### Pasajeros top 10 rutas

Pasajeros solo para las 10 rutas más grandes de lo que esté filtrado; el resto queda en blanco y no se dibuja.

Formato: `#,0`

```dax
Pasajeros top 10 rutas =
IF (
    RANKX ( ALLSELECTED ( Rutas[Nombre ruta] ), [Pasajeros],, DESC, DENSE ) <= 10,
    [Pasajeros]
)
```

### Pasajeros internacionales top 10 países

Pasajeros internacionales de los 10 países con más viajeros.

Formato: `#,0`

```dax
Pasajeros internacionales top 10 países =
IF (
    NOT ISBLANK ( [Pasajeros internacionales] )
        && RANKX ( ALLSELECTED ( Trafico[País exterior] ), [Pasajeros internacionales],, DESC, DENSE ) <= 10,
    [Pasajeros internacionales]
)
```

### Pasajeros internacionales top 10 rutas

Pasajeros internacionales de las 10 rutas internacionales más grandes.

Formato: `#,0`

```dax
Pasajeros internacionales top 10 rutas =
IF (
    NOT ISBLANK ( [Pasajeros internacionales] )
        && RANKX ( ALLSELECTED ( Rutas[Nombre ruta] ), [Pasajeros internacionales],, DESC, DENSE ) <= 10,
    [Pasajeros internacionales]
)
```

## Temporadas

### Índice de temporada

Pasajeros del mes / promedio mensual de su año x 100, promediado de 2022 a 2025. 100 = un mes normal. Ignora el filtro de año: 2020 y 2021 tienen la pandemia y 2026 no está completo.

Formato: `0.0`

```dax
Índice de temporada =
VAR anios =
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
    AVERAGEX ( indices, [@indice] )
```

### Mes más fuerte

El mes con el índice de temporada más alto.

```dax
Mes más fuerte =
VAR meses = ADDCOLUMNS ( SUMMARIZE ( ALL ( Calendario ), Calendario[Mes], Calendario[Mes largo] ), "@i", [Índice de temporada] )
RETURN
    MAXX ( TOPN ( 1, meses, [@i], DESC ), Calendario[Mes largo] )
```

### Mes más flojo

El mes con el índice de temporada más bajo.

```dax
Mes más flojo =
VAR meses = ADDCOLUMNS ( SUMMARIZE ( ALL ( Calendario ), Calendario[Mes], Calendario[Mes largo] ), "@i", [Índice de temporada] )
RETURN
    MAXX ( TOPN ( 1, meses, [@i], ASC ), Calendario[Mes largo] )
```

## Carga

### Carga que sale (t)

Toneladas en vuelos internacionales que salen de Colombia.

Formato: `#,0`

```dax
Carga que sale (t) =
CALCULATE ( [Carga (t)], Trafico[Sentido] = "Sale de Colombia" )
```

### % carga internacional

Parte de las toneladas que va en vuelos internacionales.

Formato: `0.0%`

```dax
% carga internacional =
DIVIDE (
    CALCULATE ( [Carga (t)], TipoTrafico[Tráfico] = "Internacional" ),
    CALCULATE ( [Carga (t)], REMOVEFILTERS ( TipoTrafico ) )
)
```

### Índice de carga

Como el índice de temporada, pero con toneladas. 100 = un mes normal (2022 a 2025).

Formato: `0.0`

```dax
Índice de carga =
VAR anios =
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
    AVERAGEX ( indices, [@indice] )
```

### Carga top 8 rutas

Toneladas solo para las 8 rutas con más carga.

Formato: `#,0`

```dax
Carga top 8 rutas =
IF (
    RANKX ( ALLSELECTED ( Rutas[Nombre ruta] ), [Carga (t)],, DESC, DENSE ) <= 8,
    [Carga (t)]
)
```

### Carga top 6 aerolíneas

Toneladas solo para las 6 aerolíneas con más carga.

Formato: `#,0`

```dax
Carga top 6 aerolíneas =
IF (
    RANKX ( ALLSELECTED ( Aerolineas[Aerolínea] ), [Carga (t)],, DESC, DENSE ) <= 6,
    [Carga (t)]
)
```
