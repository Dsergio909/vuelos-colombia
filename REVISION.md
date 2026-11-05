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

## Mejora 2: el README contra el tablero real, y una prueba para los conteos

Mientras esperaba turno de Power BI, comparé el README con lo que de verdad genera `powerbi/generar_tablero.py`. Encontré **6 cosas desfasadas**:

1. Decía "cinco páginas"; el tablero tiene **6** (la sexta es "Control de datos").
2. Decía que había filtro por aerolínea; solo hay **2** filtros: año y tráfico.
3. Decía que el tablero era un `.pbix`; es un proyecto en texto `.pbip`. Las instrucciones para abrirlo apuntaban a `datos/fuente` y el parámetro espera la carpeta `datos`.
4. No citaba **OurAirports**, de donde salen las coordenadas del mapa (dominio público). Ahora sí, y la estructura del repo muestra `datos/referencia/` y el script de coordenadas.
5. **Prueba nueva** (`test_conteos_del_readme`): cuenta las pruebas y las consultas de análisis y revisa que el README diga esos números. Ya se habían desfasado dos veces a mano. En su primera corrida atrapó un error: el README decía **11** consultas de análisis y son **10** (la 18 pasó a ser la 99).
6. La estructura decía "10 a 19 análisis"; van de la 10 a la 20 (la 20 es el informe de calidad).

Resultado: **38 pruebas pasan** (antes 37), 2 se corren a mano.

## Vuelta 3 de errores: el tablero contra el SQL

Con mi turno de Power BI (sin tocar la pantalla para esta parte): abrí el proyecto, actualicé el modelo tabla por tabla desde PowerShell y corrí consultas DAX contra el motor de Power BI.

- **El refresco ya no se cuelga:** el modelo completo cargó en unos **85 segundos** (antes pasaba de 30 minutos y hubo que cancelarlo). La tabla más lenta es Rutas, con 28 a 32 segundos.
- **56 de 56 cifras iguales al SQL:** pasajeros totales, nacionales e internacionales, carga y carga internacional, ocupación nacional y HHI de cada año de 2020 a 2026, más filas (465.760), aeropuertos (1.438), índices de diciembre (110,7), febrero (88,4) y carga que sale en abril (126,6), Bogotá - Medellín 2025 y la parte de JetSMART. Las 10 rutas nacionales de 2025 salen en el mismo orden que `resultados/11_rutas_principales.csv`.
- Solo el 0,38 % de los pasajeros por aeropuerto cae en aeropuertos sin coordenadas.

## Diseño: mirar cada página como la vería un reclutador

Revisé las 6 páginas en pantalla. Encontré 5 problemas:

1. **El mapa salía vacío:** Azure Maps pide iniciar sesión con una cuenta. Lo cambié por un gráfico de dispersión con latitud y longitud, sin ejes, con los **12** aeropuertos de Colombia con más pasajeros y sus nombres. Se reconoce la forma del país (San Andrés arriba a la izquierda, Bogotá como el círculo más grande). Tres medidas nuevas: 26 en total.
2. **El filtro de año cortaba las gráficas "por año":** en Aerolíneas y en Nacional e internacional, las barras y las líneas de 2020 a 2026 mostraban solo 2025. Ahora el filtro de año no las toca (`visualInteractions` con `NoFilter`).
3. **Listas cortadas:** los "top 10" de países y rutas internacionales mostraban 9 y pedían barra de desplazamiento; en Carga se veían 7 de 10 rutas y 7 de 8 aerolíneas. Ajusté los tamaños y en Carga pasé a 8 rutas y 6 aerolíneas, que caben completas.
4. **Carga en "0,39 mill.":** ahora las barras dicen las toneladas enteras (388.785) y no tienen eje repetido.
5. **La línea importante no se distinguía:** en el índice de carga, "Sale de Colombia" (la del pico de abril) va con el color de acento y las otras dos en gris claro.

También aclaré en la página de control que su ocupación junta nacional e internacional.

Entregables: `docs/tablero.pdf` (6 páginas, 436 KB) y 5 capturas en `capturas/`, sacadas de ese mismo PDF con Inkscape (sin los paneles de Power BI). No guardé `.pbix`: el proyecto en texto (`.pbip`) es la fuente y se puede revisar línea por línea en GitHub.

## Auditoría externa: Antigravity (Gemini) y la sesión principal

Sergio pidió auditarlo como los otros proyectos. Antigravity revisó el SQL y el README en 2 partes; la sesión principal comprobó cada hallazgo contra `datos/vuelos.duckdb` y revisó una copia limpia (38 pruebas, sin claves ni datos privados). Confirmaron el HHI, las participaciones, los índices de temporada, la ocupación como razón de sumas, que 2026 no se compara contra años completos y que el pronóstico no usa datos del futuro. **Ninguna cifra del README estaba mal.** Lo que arreglé:

1. **Tabla `rutas` (02_limpiar.sql):** agrupaba solo por código de ruta y tomaba cualquier nombre. Hay códigos que son un aeropuerto de Colombia y otro del exterior (IDA es Puerto Inírida e Idaho; AGU es Aguazul y Aguascalientes), y 63 rutas mezclaban nacional e internacional. Ahora la clave es **ruta + tráfico** (7.188 rutas en vez de 7.125) y, si una ruta trae dos nombres, gana el de más pasajeros. Probé también la clave con el país de cada extremo y la descarté: separa de más, porque el mismo país viene escrito de dos formas (KOREA y COREA, BERMUDA e ISLAS CARIBE). En Power BI, `Rutas` usa la misma clave (`Clave ruta`). **Prueba nueva:** BOG-IDA nacional es Bogotá - Puerto Inírida e internacional es Bogotá - Idaho; AGU-BOG, Aguazul o Aguascalientes. No cambió ninguna cifra publicada: el top 15 de rutas sale igual.
2. **Tráfico que no cuadra con los países:** 19 filas "nacionales" de 2022 salen de México (Aeroméxico, 138 pasajeros). Ahora el alcance es explícito: nacional = los dos extremos en Colombia; internacional = uno solo. Quedan fuera **29 filas** (estas 19 más las 10 de carga ya conocidas), igual en SQL, Power Query y en la tabla `eq` (allí hay 0). Cambió solo 2022: 138 pasajeros nacionales menos (32.719.831), y ninguna cifra del README.
3. **99_cifras_clave.sql:** el primer semestre de 2026 ahora también lleva `mes <= 6` en el numerador. Hoy da igual, pero con la próxima descarga habría comparado más de 6 meses contra 6.
4. **16_ocupacion.sql:** nueva columna `meses`; 2026 sale con 6 y el comentario explica que no se compara con años completos. En la página de control del tablero hay una columna "Meses" (medida nueva `Meses con datos`: 27 medidas).
5. **README, conclusión 3:** aclara que Aerocivil cuenta pasajeros por tramo de vuelo; quien hace escala en Bogotá cuenta en los dos tramos. La cifra (69,5 %) no cambia. También explica las 29 filas y la clave de las rutas.
6. **Controles de calidad (20_controles_calidad.sql):** de 12 a **17**. El de tildes ahora revisa país de origen y de destino; nuevos: rutas repetidas y cuatro de `eq` (fechas, negativos, tráfico que no cuadra y meses). Los 17 pasan.
7. **Correo de los commits:** salían con el Gmail de Sergio; ahora usan su correo privado de GitHub (`noreply`), también en la configuración local del repo. La rama nunca estuvo en GitHub.

Descartado por la sesión principal (no era real): filas de `eq` con sillas en 0 y pasajeros, o con más pasajeros que sillas (hay 0), y aeropuertos de Bogotá clasificados como punto a punto (4 pasajeros en 2025).

Resultado: **39 pruebas pasan** (antes 38) y la copia limpia da los mismos resultados. Con un turno corto de Power BI: **56 de 56 cifras del tablero iguales al SQL** (ya con los 138 pasajeros menos de 2022), 7.188 rutas en los dos, 2026 con 6 meses en la página de control y BOG-IDA como Bogotá - Puerto Inírida (nacional) y Bogotá - Idaho (internacional). PDF y capturas exportados de nuevo.

## Revisión de la nube (primera vuelta)

La nube clonó el repo como un desconocido: 39 de 39 pruebas, resultados idénticos y Actions en verde. Recalculó con su propio SQL las 32 cifras del README y las 3 del encabezado del tablero (todas coinciden) y rehízo el pronóstico en Python (3,4 %, 12,0 % y 18,2 millones). Privacidad limpia. Pidió estos arreglos; comprobé cada uno contra los datos antes de cambiar:

1. **"Las rutas punto a punto eran las de Viva" era exagerado.** En 2022 Viva llevaba el **31,7 %** de los pasajeros de las rutas que no pasan por Bogotá: era la aerolínea más grande ahí, pero Avianca tenía 22,8 % y LATAM 21,9 %. El README ahora da la cifra (español e inglés) y sale de `99_cifras_clave.sql`, así que la prueba del README la exige.
2. **"La mitad va en Bogotá - Miami"** pasó a "casi la mitad" (47,5 %) en los dos idiomas.
3. **Licencia leída de la fuente, no escrita a mano.** Confirmé desde el PC en los metadatos de datos.gov.co que los dos conjuntos dicen `CC_40_BY_SA` (Creative Commons Attribution Share Alike 4.0), atribución Aerocivil. `descargar_datos.py` la lee de `api/views/<id>.json` y la guarda en `descarga.json` (opción nueva `--solo-licencia`, que no toca los datos). Pruebas nuevas: 2 sin internet (la licencia guardada) y 2 en vivo (que no cambió).
4. **Avisos de licencia de los datos:** `datos/LICENSE.md` y `resultados/LICENSE.md` (como Olist), una nota al final de `LICENSE` (MIT solo cubre el código) y una línea en los dos README.
5. **CLAUDE.md** manda a leer `Proyectos/Vuelos Colombia.md`, `Proyectos/Como trabajar con Sergio.md` y el plan, como los otros repos.
6. **Ocupación 81,0 % contra 81,5 %:** las dos están bien. La tarjeta del tablero ahora dice "Ocupación del tráfico elegido" y el README explica que con nacional e internacional juntos da 81,0 % (cifra nueva en `99_cifras_clave.sql`, con su prueba).

Opcionales: el mapa pasó a 10 aeropuertos (los nombres de Medellín Rionegro y Olaya Herrera se cruzaban), las barras dan más espacio al nombre de la ruta, y el README trae el comando para activar el entorno en Windows. No hice `.pbix`: guardaría los datos dentro y el `.pbip` ya es la fuente.

Pruebas en vivo corridas en el PC (la nube no pudo por la red): **4 de 4 pasan**; la fuente no cambió desde la copia del 4 de noviembre. Resultado: **41 pruebas automáticas pasan**, más 4 en vivo. El tablero, actualizado, sigue dando **56 de 56 cifras iguales al SQL**.

## Revisión de la nube (segunda vuelta)

La nube confirmó los arreglos de la primera vuelta (41 de 41 pruebas, Viva 31,68 %, ocupación total 81,04 %, licencia, avisos, CLAUDE.md y privacidad de los 11 commits). Quedaban 2 arreglos visibles:

1. **Etiqueta ilegible en la página 4:** la de Bogotá - Madrid («1,26 mill.») quedaba dentro de la barra, verde oscuro sobre verde oscuro. Ahora las 5 gráficas de barras ponen la etiqueta siempre afuera (`OutsideEnd`) y el eje termina en **1,15 veces la barra más grande de lo que esté filtrado** (5 medidas nuevas en la carpeta `Ejes`: 32 medidas). Como es una medida, sirve para cualquier año. Lo revisé en pantalla con **2022, 2024, 2025 y 2026** en las páginas 1, 4 y 5 (la 3 no tiene barras con etiqueta): ninguna etiqueta quedó adentro ni cortada. Los nombres largos de aerolíneas de carga también se ven completos.
2. **Nombres del mapa encimados:** el problema de fondo era San Andrés, tan al oeste que apretaba todo el continente en un rincón. El recuadro ahora es fijo en la Colombia continental (el título dice que San Andrés queda fuera), las burbujas son algo más chicas y Medellín sale como «Medellín» (Olaya Herrera no entra entre los 10). Ya no se cruzan Barranquilla, Santa Marta ni Medellín con Bogotá. Probé primero burbujas mucho más chicas y no bastaba: Barranquilla seguía tapando a Santa Marta.
3. Opcional: partí las 2 frases largas del README (la del HHI y la del pronóstico), en los dos idiomas. La etiqueta «26,3 %» de la página 4 la dejé como está.

Resultado: 41 pruebas pasan, el tablero sigue con **56 de 56 cifras iguales al SQL**, y el PDF y las capturas se exportaron otra vez con el filtro en 2025.

## Pendiente

- Que Sergio vea el antes y el después y dé su «sí» para crear el repo en GitHub.
- Ver las pruebas en verde en GitHub Actions.
