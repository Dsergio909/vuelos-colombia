// Tabla de hechos: vuelos, sillas y pasajeros a bordo (para la ocupación).
// Se agrupa por mes, aerolínea, ruta, tráfico y tipo de vuelo para que pese menos.
let
    Origen = EQ_crudo,
    SoloColombia = Table.SelectRows(Origen, each [tr_fico] = "N" or [tr_fico] = "I"),
    // Solo vuelos que salen o llegan a Colombia (país sin tildes; la función corre una vez por país distinto)
    PaisesCrudos = List.Buffer(List.Distinct(List.Transform(List.Combine({SoloColombia[pais_origen], SoloColombia[pais_destino]}), each _ ?? ""))),
    PaisLimpio = Record.FromList(List.Transform(PaisesCrudos, fnQuitarTildes), PaisesCrudos),
    TocaColombia = Table.SelectRows(SoloColombia,
        each Record.FieldOrDefault(PaisLimpio, [pais_origen] ?? "", null) = "COLOMBIA"
          or Record.FieldOrDefault(PaisLimpio, [pais_destino] ?? "", null) = "COLOMBIA"),
    Columnas = Table.SelectColumns(TocaColombia, {"a_o", "mes", "sigla_empresa", "origen", "destino", "tr_fico",
        "tipo_vuelo", "n_mero_de_vuelos", "sillas_ofrecidas", "pasajeros_a_bordo", "carga_correo_a_bordo_kg"}),
    Tipos = Table.TransformColumnTypes(Columnas, {{"a_o", Int64.Type}, {"mes", Int64.Type},
        {"n_mero_de_vuelos", Int64.Type}, {"sillas_ofrecidas", Int64.Type}, {"pasajeros_a_bordo", Int64.Type},
        {"carga_correo_a_bordo_kg", type number}}, "en-US"),
    Vacios = Table.ReplaceValue(Tipos, null, 0, Replacer.ReplaceValue,
        {"n_mero_de_vuelos", "sillas_ofrecidas", "pasajeros_a_bordo", "carga_correo_a_bordo_kg"}),
    Codigos = Table.TransformColumns(Vacios, {{"sigla_empresa", each Text.Upper(Text.Trim(_)), type text},
        {"origen", each Text.Upper(Text.Trim(_)), type text}, {"destino", each Text.Upper(Text.Trim(_)), type text}}),
    Fecha = Table.AddColumn(Codigos, "Fecha", each #date([a_o], [mes], 1), type date),
    Ruta = Table.AddColumn(Fecha, "Ruta",
        each if [origen] < [destino] then [origen] & "-" & [destino] else [destino] & "-" & [origen], type text),
    Palabras = Table.TransformColumns(Ruta, {
        {"tr_fico", each if _ = "N" then "Nacional" else "Internacional", type text},
        {"tipo_vuelo", each Record.FieldOrDefault(
            [R = "Regular", T = "Taxi aéreo", C = "Chárter", A = "Adicional", N = "No regular"], _, _), type text}}),
    // La ocupación solo usa filas con sillas reportadas (los taxis aéreos reportan 0 sillas)
    ConSillas = Table.AddColumn(Palabras, "pax_con_sillas",
        each if [sillas_ofrecidas] > 0 then [pasajeros_a_bordo] else 0, Int64.Type),
    Agrupado = Table.Group(ConSillas, {"Fecha", "sigla_empresa", "Ruta", "tr_fico", "tipo_vuelo"}, {
        {"Vuelos", each List.Sum([n_mero_de_vuelos]), Int64.Type},
        {"Sillas", each List.Sum([sillas_ofrecidas]), Int64.Type},
        {"Pasajeros a bordo", each List.Sum([pasajeros_a_bordo]), Int64.Type},
        {"Pasajeros con sillas", each List.Sum([pax_con_sillas]), Int64.Type},
        {"Carga a bordo kg", each List.Sum([carga_correo_a_bordo_kg]), type number}}),
    Final = Table.RenameColumns(Agrupado, {{"sigla_empresa", "Sigla"}, {"tr_fico", "Tráfico"}, {"tipo_vuelo", "Tipo de vuelo"}})
in
    Final
