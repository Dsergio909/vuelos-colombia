# Flights in Colombia: routes, seasons and airlines

[Versión en español](README.md) · ![Tests](https://github.com/Dsergio909/vuelos-colombia/actions/workflows/pruebas.yml/badge.svg)

I wanted to know which routes carry the most passengers and cargo in Colombia, which months are busiest and which airlines fly them. I took the open data from Aerocivil (Colombia's civil aviation authority), January 2020 to June 2026, cleaned it with SQL and Power Query and built a Power BI dashboard.

![Dashboard: overview and routes](capturas/01_resumen_rutas.png)

## What I found

**1. The domestic market didn't grow. All the growth was international.**
Between 2022 and 2025 domestic passengers went from 32.7 to 32.9 million: only 0.4% more. International passengers went from 15.2 to 24.7 million, 61.9% more. International traffic is now 42.9% of all passengers, up from 31.8% in 2022. Note: in the first half of 2026 domestic traffic did grow, 6.1% compared with the same half of 2025. We'll see if it holds.

**2. When Viva Air and Ultra Air stopped flying, Avianca and LATAM took the market. Then JetSMART arrived.**
In 2022 Viva and Ultra had 24.7% of domestic passengers. In the data, Viva reports until February 2023 and Ultra until March. That year Avianca and LATAM (with their subsidiaries) went from 62.3% to 77.9%. The HHI concentration index rose from 2,483 to 3,219, and above 2,500 a market is considered highly concentrated. By 2025 JetSMART had 13.5%, Avianca and LATAM were down to 68.7% and the HHI was 2,738.

**3. Almost everything goes through Bogotá, but the routes that are growing don't.**
69.5% of domestic passengers in 2025 flew a route that starts or ends at El Dorado. Note: Aerocivil counts passengers per flight leg, so someone flying from Cali to Cartagena with a stop in Bogotá counts on both legs. The biggest route is Bogotá - Medellín, with 4.0 million passengers in 2025. On point-to-point routes (for example Medellín - Cartagena or Cali - Cartagena), Viva was the biggest airline: in 2022 it carried 31.7% of their passengers, almost a third. Those routes fell 20.4% between 2022 and 2024. In 2025 they grew 5.2%, while Bogotá routes fell 3.8%.

**4. December is the strongest month and February the weakest.**
With an index where 100 is a normal month, December scores 110.7 on domestic flights and February 88.4 (2022 to 2025 average). So December moves 25% more passengers than February. July and August are the second peak season. If I had to plan capacity or staff, that's where I'd look first.

**5. Air cargo is international, leaves through Bogotá to Miami and peaks in April.**
85.1% of the tonnes in 2025 flew on international flights. The Bogotá - Miami route alone carried 47.5% of that international cargo. Cargo leaving Colombia peaks in April, with an index of 126.6. The data doesn't say what is shipped, but the peak matches the flower season before Mother's Day. That's a hypothesis, not a fact from the data.

**A simple forecast for the second half of 2026.**
With the seasonal index of the three previous years and the actual January to June numbers, I built a July to December forecast. First I tested it on 2025, as if I didn't know what happened. For domestic it was off by 3.4% per month on average; for international, by 12.0%. That's because the base years still carry the post-pandemic recovery. So I only trust the domestic one: for July to December 2026 it gives 18.2 million passengers. The calculation is in [sql/19_pronostico.sql](sql/19_pronostico.sql).

One more: on regular domestic flights planes are 81.5% full (2025), based on the seats offered that Aerocivil reports. Adding international flights gives 81.0%, which is the number the dashboard shows when traffic isn't filtered.

## The dashboard

Five pages, one per question, plus a sixth control page that shows the totals by year so they can be checked against the SQL. One accent color and two filters on top: year and traffic (domestic or international).

| Page | What it answers |
|---|---|
| Overview and routes | How many passengers, how much cargo, the top 10 routes and the 10 largest airports placed by latitude and longitude (San Andrés is outside the frame) |
| Seasons | Which months are busiest (index 100 = normal month) |
| Airlines | Who has which share of the market and how it changed since 2022 |
| Domestic and international | How each one grows and which countries people fly to |
| Cargo | Tonnes by route, by direction (outbound or inbound) and by month |

![Seasons](capturas/02_temporadas.png)
![Airlines](capturas/03_aerolineas.png)
![Domestic and international](capturas/04_nacional_internacional.png)
![Cargo](capturas/05_carga.png)

Full dashboard as PDF: [docs/tablero.pdf](docs/tablero.pdf). The DAX measures can be read without Power BI in [dax/medidas.md](dax/medidas.md) and the Power Query cleaning in [powerquery/](powerquery/). The dashboard itself is in Spanish.

## Where the data comes from

Unidad Administrativa Especial de Aeronáutica Civil (Aerocivil), published on datos.gov.co under [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/):

- [Commercial Air Transport: Origin-Destination Traffic](https://www.datos.gov.co/d/gb6w-ynu4) (`gb6w-ynu4`): 478,010 rows. Airline, month, origin and destination airport, domestic or international, passengers and cargo plus mail in kilos.
- [Air Transport: Traffic by Aircraft Type](https://www.datos.gov.co/d/djjf-g4q4) (`djjf-g4q4`): 216,599 rows. The same by aircraft type, with flights, hours and seats offered. Load factor comes from here.

Things to keep in mind:

- **Figures for 2022 to 2025 are provisional.** Aerocivil may correct them. That's why the repo has a fixed copy, downloaded on November 4, 2026, and a test that warns if the source changed.
- **2026 only goes to June.** 2026 is not compared against full years.
- **2020 and 2021 are distorted by the pandemic** (from April to August 2020 there were almost no passenger flights). Seasons are calculated with 2022 to 2025.
- **Only traffic to, from or within Colombia.** I removed 12,240 rows of "Special" traffic: flights between two foreign countries, like Panama - Havana, run by a Colombian airline. I also removed 29 rows whose traffic type doesn't match the countries: 10 cargo rows marked as international that never touch Colombia (Montevideo - Ezeiza, for example) and 19 marked as domestic that depart from Mexico (138 passengers in 2022). And since the same code can be an airport in Colombia and another one abroad (IDA is Puerto Inírida and also Idaho), each route is identified by its two codes and by whether it is domestic or international.
- **Cargo includes mail**, because that's how Aerocivil reports it.
- I added the brand name for the big airlines (for example, AIRES is LATAM Colombia and FAST COLOMBIA was Viva Air) in a short list inside [sql/02_limpiar.sql](sql/02_limpiar.sql). The rest use the name they report.

Airport coordinates for the map come from [OurAirports](https://ourairports.com/data/) (public domain), matched by IATA code in [scripts/coordenadas_aeropuertos.py](scripts/coordenadas_aeropuertos.py).

Derived data in this repo (the copy in `datos/fuente/`, the CSVs in `resultados/`, the PDF and the screenshots) keeps the same CC BY-SA 4.0 license: see [datos/LICENSE.md](datos/LICENSE.md) and [resultados/LICENSE.md](resultados/LICENSE.md). The code is MIT. I didn't type the license by hand: `scripts/descargar_datos.py` reads it from each dataset's metadata and a test checks it hasn't changed.

## How I built it

1. **Data:** a script downloads both datasets from the datos.gov.co API (no key, 50,000 rows per page, with retries) and checks that every row arrived.
2. **Cleaning in SQL (DuckDB):** types, 52 rows with no passengers that I count as 0 and flag, cities written two ways ("CALI" and "SANTIAGO DE CALI"), one airline with several names, and routes without direction (Bogotá - Medellín adds both ways).
3. **Queries:** 10 analysis queries in numbered, commented `.sql` files (including a data quality report and the forecast), with CTEs and window functions (`rank`, `lag`, shares and running totals).
4. **Tests:** 41 tests that run on GitHub Actions on every change, plus 4 that run on demand against the live API (totals and license). They check that yearly totals match the ones the API itself calculates, that cleaning doesn't lose or duplicate rows and that every number in this README comes from the data.
5. **Power BI:** Power Query reads the same copy and cleans it with the same steps. DAX measures and the six pages go on top.

I defined the plan and the questions. The code was written by Claude (AI) and I checked every number against the source.

```
sql/          numbered queries (01 load, 02 clean, 10 to 20 analysis and quality, 99 README numbers)
scripts/      descargar_datos.py (download), correr_sql.py (run queries) and coordenadas_aeropuertos.py (map)
tests/        pytest tests
datos/fuente/ fixed copy of the Aerocivil data in Parquet (6 MB) and its official totals
datos/referencia/ airport coordinates (OurAirports)
resultados/   what each query returns, as CSV
powerbi/      the dashboard as a Power BI project in text (.pbip)
powerquery/   the Power Query cleaning, as text
dax/          the DAX measures, as text
capturas/     dashboard screenshots
docs/         the dashboard as PDF
```

## How to run it

You need Python 3.12.

```bash
git clone https://github.com/Dsergio909/vuelos-colombia.git
cd vuelos-colombia
python -m venv .venv
.venv\Scripts\activate       # Windows; on Linux or Mac: source .venv/bin/activate
pip install -r requirements.txt
python -m pytest              # tests
python scripts/correr_sql.py  # recalculates resultados/
```

To download the latest Aerocivil data: `python scripts/descargar_datos.py` (about 2 minutes). To compare the copy against the live API: `python -m pytest -m en_linea`.

To open the dashboard: Power BI Desktop (free). Open `powerbi/vuelos-colombia.pbip`, set the `CarpetaDatos` parameter in Power Query to the `datos` folder of your copy of the repo and click **Refresh**.

## What's missing

- The data has no fares, delays or cancellations. You can't tell if a route is profitable or how punctual an airline is.
- It doesn't say what kind of cargo is shipped either. The link between the April peak and flowers is a hypothesis.
- Routes are between airports. A passenger flying Cali to Madrid through Bogotá may show up as two legs.
- The forecast is simple on purpose. A model with trend or more years would work better for international.
- The map has no country outline behind it. The Power BI map (Azure Maps) asks you to sign in with an account, so I used a scatter chart with each airport's latitude and longitude. It reads the same and anyone can open it. The frame shows only mainland Colombia: with San Andrés, far to the west, the names on the coast ended up on top of each other.

## How to explain it in 2 minutes

"I took the open data from Aerocivil: almost 700,000 rows of flights from 2020 to June 2026. The question was which routes, which months and which airlines move the country's people and cargo.

First I cleaned it with SQL, in DuckDB. There were cities written two ways, rows with no passengers and airlines with several names. I left automated tests that compare my totals with the source, so I know I didn't lose or invent anything.

Three things stood out. One, since 2022 the domestic market is flat and all the growth is international. Two, when Viva Air and Ultra Air left in 2023, Avianca and LATAM went from 62% to 78% of domestic passengers, and the routes that don't go through Bogotá dropped. JetSMART is winning part of that back. Three, cargo is almost all international, almost half of it flies Bogotá - Miami and it peaks in April.

All of that is in a five-page Power BI dashboard, one page per question. If this were an airline or an airport, I'd use it to plan capacity and staff by season."

## License

Code: MIT. Data: Aerocivil, CC BY-SA 4.0 ([datos/LICENSE.md](datos/LICENSE.md) and [resultados/LICENSE.md](resultados/LICENSE.md)). The MIT license does not cover the data.
