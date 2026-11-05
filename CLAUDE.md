# vuelos-colombia · instrucciones para Claude Code

Proyecto 4 del plan de portafolio de datos de Sergio: rutas, temporadas y aerolíneas de Colombia con datos de Aerocivil, SQL (DuckDB) y Power BI.

## Antes de empezar
- En el PC: lee en el cerebro de Obsidian `Proyectos/Vuelos Colombia.md`, `Proyectos/Como trabajar con Sergio.md` y `Proyectos/Plan datos y n8n.md` (sección «4. Vuelos en Colombia» y las reglas de todos los repos). Si vas a escribir texto público, lee también `Personal/Mi_voz_al_escribir.md`.
- En la nube: el cerebro solo se lee (repo privado `cerebro`); al terminar entrega un paquete en Markdown para que Sergio lo aplique desde el PC.

## Reglas de este repo
- Las cifras del README salen de `resultados/99_cifras_clave.csv`. Si cambias el SQL, corre `python scripts/correr_sql.py` y actualiza los dos README: `pytest` falla si una cifra o un conteo no coincide.
- `datos/fuente/` es la copia fija de Aerocivil (CC BY-SA 4.0, con atribución; ver `datos/LICENSE.md`). `datos/crudos/` no se sube.
- El tablero se genera con `python powerbi/generar_tablero.py` (Power Query en `powerquery/`); después de cambiarlo, compara sus cifras con el SQL.
- Solo una tarea pesada a la vez en el PC (Power BI, Ollama, n8n).

## Registro de carrera
Al cerrar ("cierra el chat") o cuando diga "registra esto", revisa si pasó algo que cumpla al menos uno de estos criterios: terminé o entregué algo, tomé una decisión importante con su razón, obtuve un resultado concreto, aprendí una herramienta usándola de verdad, o algo falló y entendí por qué. Si nada cumple, dime "nada para registrar".

- En mi Google Drive, carpeta Cerebro: Carrera/REGISTRO.md (registro) y Carrera/00_Carrera.md (formato).
- Si aparece una copia que dice "Este cerebro se mudó" (por ejemplo, en la carpeta vieja `Cerebro_Carrera`), ignórala.

Puedes escribir la entrada tú mismo: agrégala al final de REGISTRO.md sin editar ni borrar las anteriores, y confírmame en una línea. Si tu herramienta no puede agregar al final sin reemplazar el archivo completo o crear uno nuevo (por ejemplo, el conector de Drive desde la nube), no lo hagas: entrégame la entrada en un bloque de código para que yo la pegue.

Si no puedes leer 00_Carrera.md, usa este formato:

```markdown
## AAAA-MM-DD · <Proyecto> · <título corto>
- Qué hice:
- Problema que resuelve:
- Herramientas:
- Resultado o evidencia: (si no hay cifra real, no se inventa)
- Qué aprendí o qué falló:
- ¿Lo puedo defender en entrevista?: sí / parcial (qué me falta)
- ¿Se puede mostrar en público?: sí / no / solo sin datos internos
```

Máximo 8 líneas. Sin cifras inventadas, sin datos de terceros, sin claves ni rutas privadas.
