// Tabla de hechos: una fila por aerolínea, mes, ruta, tráfico y tipo de vuelo.
// Mismos pasos que sql/02_limpiar.sql.
let
    Origen = OD_crudo,
    // 1. Solo tráfico de Colombia: N (nacional) e I (internacional). La E (especial) son vuelos entre dos países extranjeros.
    SoloColombia = Table.SelectRows(Origen, each [tr_fico_n_i] = "N" or [tr_fico_n_i] = "I"),
    Columnas = Table.SelectColumns(SoloColombia, {"sigla_empresa", "a_o", "n_mero_de_mes", "origen", "pais_origen",
        "destino", "pais_destino", "tr_fico_n_i", "tipo_vuelo", "pasajeros", "carga_correo_kg"}),
    Nombres = Table.RenameColumns(Columnas, {
        {"sigla_empresa", "Sigla"}, {"a_o", "Año"}, {"n_mero_de_mes", "Mes"}, {"origen", "Origen"},
        {"pais_origen", "País origen"}, {"destino", "Destino"}, {"pais_destino", "País destino"},
        {"tr_fico_n_i", "Tráfico"}, {"tipo_vuelo", "Tipo de vuelo"}, {"pasajeros", "Pasajeros"}, {"carga_correo_kg", "Carga kg"}}),
    // 2. Países sin tildes: llegan "PANAMA" y "PANAMÁ". Para que sea rápido, la función corre una vez
    //    por cada país distinto (unos 200) y no por cada fila (casi medio millón)
    PaisesCrudos = List.Buffer(List.Distinct(List.Transform(List.Combine({Nombres[País origen], Nombres[País destino]}), each _ ?? ""))),
    PaisLimpio = Record.FromList(List.Transform(PaisesCrudos, fnQuitarTildes), PaisesCrudos),
    Textos = Table.TransformColumns(Nombres, {
        {"Sigla", each Text.Upper(Text.Trim(_)), type text}, {"Origen", each Text.Upper(Text.Trim(_)), type text},
        {"Destino", each Text.Upper(Text.Trim(_)), type text},
        {"País origen", each Record.FieldOrDefault(PaisLimpio, _ ?? "", null), type text},
        {"País destino", each Record.FieldOrDefault(PaisLimpio, _ ?? "", null), type text}}),
    // 10 filas de carga dicen "internacional" pero no tocan Colombia (por ejemplo Montevideo - Ezeiza): fuera
    TocaColombia = Table.SelectRows(Textos, each [País origen] = "COLOMBIA" or [País destino] = "COLOMBIA"),
    // 3. Tipos. Los números vienen con punto decimal: se leen con cultura en-US
    Tipos = Table.TransformColumnTypes(TocaColombia, {{"Año", Int64.Type}, {"Mes", Int64.Type},
        {"Pasajeros", Int64.Type}, {"Carga kg", type number}}, "en-US"),
    // 4. 52 filas sin pasajeros (casi todas de taxi aéreo con carga): cuentan como 0
    PasajerosVacios = Table.ReplaceValue(Tipos, null, 0, Replacer.ReplaceValue, {"Pasajeros"}),
    Fecha = Table.AddColumn(PasajerosVacios, "Fecha", each #date([Año], [Mes], 1), type date),
    // 5. Códigos de una letra a palabras
    Palabras = Table.TransformColumns(Fecha, {
        {"Tráfico", each if _ = "N" then "Nacional" else "Internacional", type text},
        {"Tipo de vuelo", each Record.FieldOrDefault(
            [R = "Regular", T = "Taxi aéreo", C = "Chárter", A = "Adicional", N = "No regular"], _, _), type text}}),
    // 6. Ruta sin dirección: BOG-MDE y MDE-BOG son la misma ruta
    Ruta = Table.AddColumn(Palabras, "Ruta",
        each if [Origen] < [Destino] then [Origen] & "-" & [Destino] else [Destino] & "-" & [Origen], type text),
    Sentido = Table.AddColumn(Ruta, "Sentido",
        each if [Tráfico] = "Nacional" then "Nacional"
             else if [País origen] = "COLOMBIA" then "Sale de Colombia" else "Entra a Colombia", type text),
    // Para mostrar el país con sus tildes
    ConTildes = [ESPANA = "España", MEXICO = "México", PERU = "Perú", PANAMA = "Panamá", CANADA = "Canadá",
        #"REPUBLICA DOMINICANA" = "República Dominicana", #"ESTADOS UNIDOS" = "Estados Unidos",
        #"ANTILLAS HOLANDESAS" = "Antillas Holandesas (Aruba y Curazao)", HAITI = "Haití", BELGICA = "Bélgica",
        #"EMIRATOS ARABES UNIDOS" = "Emiratos Árabes Unidos", TURQUIA = "Turquía", ALEMANIA = "Alemania"],
    PaisExterior = Table.AddColumn(Sentido, "País exterior",
        each if [Tráfico] = "Nacional" then null
             else let p = if [País origen] = "COLOMBIA" then [País destino] else [País origen]
                  in Record.FieldOrDefault(ConTildes, p, Text.Proper(p)), type text),
    // Claves para unir con Aeropuertos (el mismo código puede existir en dos países)
    ClaveOrigen = Table.AddColumn(PaisExterior, "Clave origen", each [Origen] & "|" & [País origen], type text),
    ClaveDestino = Table.AddColumn(ClaveOrigen, "Clave destino", each [Destino] & "|" & [País destino], type text),
    Final = Table.SelectColumns(ClaveDestino, {"Fecha", "Sigla", "Ruta", "Origen", "Destino", "Clave origen", "Clave destino",
        "Tráfico", "Tipo de vuelo", "Sentido", "País exterior", "Pasajeros", "Carga kg"})
in
    Final
