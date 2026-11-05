# Licencia de estos datos

Los archivos de esta carpeta no están bajo la licencia MIT del código.

- **Origen:** Unidad Administrativa Especial de Aeronáutica Civil (Aerocivil), publicados en datos.gov.co:
  - Transporte Aéreo Comercial: Tráfico Origen-Destino (`gb6w-ynu4`): https://www.datos.gov.co/d/gb6w-ynu4
  - Transporte Aéreo: Tráfico por Equipo (`djjf-g4q4`): https://www.datos.gov.co/d/djjf-g4q4
- **Licencia:** Creative Commons Atribución-CompartirIgual 4.0 Internacional (CC BY-SA 4.0): https://creativecommons.org/licenses/by-sa/4.0/deed.es. Es la que publica datos.gov.co en los metadatos de cada conjunto; `scripts/descargar_datos.py` la lee de ahí y la guarda en `fuente/descarga.json`.
- **Atribución:** Unidad Administrativa Especial de Aeronáutica Civil - AEROCIVIL, Bogotá D.C.
- **Cambios:** `fuente/` tiene los dos conjuntos tal como los entrega la API (todo como texto), pasados de CSV a Parquet y bajados el 4 de noviembre de 2026. La limpieza se hace después, en `sql/02_limpiar.sql`.
- Por la cláusula CompartirIgual, esta copia se comparte con la misma licencia CC BY-SA 4.0.
- **Excepción:** `referencia/aeropuertos_coordenadas.csv` sale de OurAirports (https://ourairports.com/data/), que publica sus datos en el dominio público.

---

The files in this folder are not covered by the MIT license of the code. `fuente/` holds a copy of two Aerocivil datasets from datos.gov.co (`gb6w-ynu4` and `djjf-g4q4`), converted from CSV to Parquet, licensed under CC BY-SA 4.0, attribution: Unidad Administrativa Especial de Aeronáutica Civil - AEROCIVIL. They are shared under the same license. `referencia/aeropuertos_coordenadas.csv` comes from OurAirports (public domain).
