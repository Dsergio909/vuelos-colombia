# Revisión por vueltas

Cómo se construyó y se revisó este proyecto, con lo que se encontró y lo que se arregló en cada vuelta.
Fecha: 4 de noviembre de 2026.

## Vuelta 0: lo mínimo de punta a punta

- Bajé los dos conjuntos de Aerocivil por la API de datos.gov.co: **478.010** filas de Origen-Destino y **216.599** de Tráfico por Equipo. Las dos cifras son iguales a las que reporta la API (`count(*)`).
- Los guardé como copia fija en Parquet (5,8 MB en total; el CSV pesaba 104 MB).
- Le pedí a la API los totales por año (filas, pasajeros, carga, vuelos, sillas) y los guardé en `datos/fuente/descarga.json`. Mi suma por año dio **exactamente** lo mismo en los 7 años y en los dos conjuntos (por ejemplo, 2025: 57.591.119 pasajeros en la API y en la copia).
- Limpieza en SQL (`sql/02_limpiar.sql`) y 9 consultas de análisis (`sql/10` a `sql/18`).
- Primeras pruebas: 32 en verde.

Lo que encontré en los datos al explorarlos:

| Hallazgo | Cuántas filas | Qué hice |
|---|---|---|
| Pasajeros vacíos (casi todo taxi aéreo con carga) | 52 | Cuentan como 0 y quedan marcados (`pasajeros_vacio`) |
| La misma ciudad escrita de dos formas ("CALI" y "SANTIAGO DE CALI", "MONTERIA" y "MONTERÍA") | 47 aeropuertos | Sin tildes, el nombre más usado por aeropuerto y una lista corta de nombres largos |
| Una sigla con dos nombres ("COPA" y "COPA AIRLINES") | 7 siglas | El nombre del último mes reportado |
| Tráfico "Especial": vuelos entre dos países extranjeros (por ejemplo Panamá - La Habana) | 12.240 | Fuera del análisis (no es tráfico de Colombia) |
| Combinaciones aerolínea + mes + ruta + tipo de vuelo repetidas | 73 (146 filas, 13.005 pasajeros) | Se dejan: a veces tienen cifras distintas y parecen reportes separados. Si se borraran, los totales ya no cuadrarían con la fuente |
| Vuelos "nacionales" con origen en México (código MTT) | 19 filas, 138 pasajeros | Se dejan como nacionales (así los clasifica Aerocivil); anotado como dato raro |

## Vuelta 1 de errores: cifras contra la fuente

1. **Error real: países con y sin tilde.** "PANAMA" y "PANAMÁ", "ESPAÑA" y "ESPANA", "PERÚ" y "PERU", "MÉXICO" y "MEXICO", "CANADÁ" y "CANADA". Partía en dos a cada país y duplicaba aeropuertos (MAD salía dos veces). **Arreglo:** los países también pasan sin tildes, en SQL y en Power Query. Los aeropuertos únicos bajaron de 1.568 a 1.438. Prueba nueva: `test_paises_sin_tildes_duplicadas`.
2. **Error real: 10 filas "internacionales" que no tocan Colombia.** Son vuelos de carga de Avianca Cargo entre otros países (por ejemplo Montevideo - Ezeiza, 1.441 toneladas en total). La consulta de carga las contaba como "entra a Colombia". **Arreglo:** el alcance ahora exige que el vuelo salga o llegue a Colombia. La carga internacional de 2022 bajó 1.441,9 t (de 737.681,7 a 736.239,8); ninguna cifra del README cambió. Prueba ajustada: `test_alcance_colombia`.
3. Empate al elegir el nombre de una ciudad: DuckDB (`mode`) y Power Query podían elegir distinto. **Arreglo:** las dos eligen el más usado y, si empatan, el primero en orden alfabético.
4. Revisado y sin error: las sumas de Origen-Destino y de Tráfico por Equipo no son iguales (Equipo da entre 6,9 % y 11,0 % más pasajeros cada año). No es un error: Equipo cuenta pasajeros a bordo de cada trayecto, incluidos los que siguen en tránsito. Por eso los pasajeros salen de Origen-Destino y la ocupación de Equipo.
5. Límite conocido: 190 rutas (0,27 % de los pasajeros) tienen un código que aparece con dos países, casi siempre por el nombre del país mal escrito ("EMIRATOS ARABE", "KOREA" y "COREA"). Se dejan así.
6. "Como un desconocido": cloné la rama en una carpeta nueva, armé un entorno nuevo, instalé `requirements.txt` y corrí todo. **36 de 36 pruebas en verde** y `resultados/` quedó idéntico (sin diferencias en git).

## Vuelta 2 de errores: privacidad y lo que dice el README

1. Búsqueda en todo el repo de rutas del PC, usuarios, correos, teléfonos, claves y tokens: no hay. Única ruta: el parámetro `CarpetaDatos` de Power Query (`C:\Trabajo\vuelos-colombia\datos`), que no tiene usuario ni nada personal. Power BI necesita una ruta completa; el README explica cómo cambiarla.
2. Marcas comerciales, revisadas en fuentes públicas: AIRES es LATAM Colombia, FAST COLOMBIA S.A.S. era Viva Air (dejó de volar el 27 de febrero de 2023), Ultra Air dejó de volar el 30 de marzo de 2023, la sigla RPB es Wingo (Aero República) y TPA es Avianca Cargo. Los datos coinciden: Viva reporta pasajeros hasta febrero de 2023 y Ultra hasta marzo.
3. **Error en el README:** decía "38 pruebas que corren en GitHub Actions", pero 2 de esas 38 solo corren a mano (contra la API en vivo). **Arreglo:** "36 pruebas con cada cambio y 2 más a mano".
4. **Error en el README:** decía "9 archivos `.sql`" y son 11 (2 de carga y limpieza y 9 de análisis). **Arreglo:** "9 consultas de análisis".
5. Comentario equivocado en `sql/12_temporadas.sql`: decía que el aeropuerto estuvo cerrado de abril a agosto de 2020. Lo que muestran los datos es que casi no hubo pasajeros (de 3.589 a 12.314 nacionales al mes, contra 2,4 millones en enero). **Arreglo:** el texto dice eso.
6. La prueba `test_readme.py` revisa que las 28 cifras clave del README (en español y en inglés) salgan de la consulta de cifras clave (hoy `sql/99_cifras_clave.sql`). Todas aparecen.

## Mejora 1: pronóstico, calidad de datos y una segunda opinión de la IA local

1. **Pronóstico simple** (`sql/19_pronostico.sql`): índice de temporada de los 3 años anteriores y el nivel real de enero a junio. Probado primero con 2025, como si no se supiera el resultado: error medio por mes de **3,4 %** en lo nacional y **12,0 %** en lo internacional. El README solo da el pronóstico nacional de julio a diciembre de 2026 (18,2 millones) y explica por qué no confía en el internacional.
2. Al hacerlo me di cuenta de que la conclusión 1 ("lo nacional no creció") estaba incompleta: en el primer semestre de 2026 lo nacional creció 6,1 % contra el mismo semestre de 2025. El README ahora lo dice.
3. **Informe de calidad de datos** (`sql/20_controles_calidad.sql`): 12 controles con lo esperado, lo obtenido y su estado. Los 12 pasan, y una prueba falla si alguno no pasa.
4. **La prueba del README atrapó un error mío:** escribí 3,3 % y 11,9 % (promedios de cifras ya redondeadas) y el cálculo exacto da 3,4 % y 12,0 %. Corregido.
5. **Segunda opinión con IA local** (Ollama, modelo `qwen3.5:4b`, 54 segundos, sin gastar cuota de Claude): le pedí revisar solo errores de inglés en `README.en.md`. Devolvió 18 sugerencias. **Acepté 3** ("International is now" pasó a "International traffic is now", "domestic did grow, 6.1% against" pasó a "domestic traffic did grow, 6.1% compared with" y "on domestic... on international" pasó a "for domestic... for international"). **Rechacé 15:** eran reescrituras de estilo que sonaban a IA ("accounted for", "dominated by"), guiones largos (la guía de voz no los usa) y una que cambiaba el sentido ("approximately 25%", cuando la cifra es exacta).

## Pendiente

- Vuelta 3 de errores: las cifras del tablero de Power BI contra el SQL (página "Control de datos").
- Vueltas de mejora y de diseño.
