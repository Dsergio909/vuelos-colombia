// Dimensión de aerolíneas: el nombre del último mes reportado y su marca comercial.
let
    Base = Table.SelectColumns(OD_crudo, {"sigla_empresa", "nombre", "a_o", "n_mero_de_mes"}),
    Tipos = Table.TransformColumnTypes(Base, {{"a_o", Int64.Type}, {"n_mero_de_mes", Int64.Type}}, "en-US"),
    Periodo = Table.AddColumn(Tipos, "Periodo", each [a_o] * 100 + [n_mero_de_mes], Int64.Type),
    Limpio = Table.TransformColumns(Periodo, {{"sigla_empresa", each Text.Upper(Text.Trim(_)), type text},
        {"nombre", Text.Trim, type text}}),
    Ordenado = Table.Buffer(Table.Sort(Limpio, {{"sigla_empresa", Order.Ascending}, {"Periodo", Order.Descending}})),
    Ultimo = Table.Distinct(Table.SelectColumns(Ordenado, {"sigla_empresa", "nombre"}), {"sigla_empresa"}),
    // Siglas que solo aparecen en Tráfico por Equipo
    Equipo = Table.TransformColumns(Table.SelectColumns(EQ_crudo, {"sigla_empresa", "nombre"}),
        {{"sigla_empresa", each Text.Upper(Text.Trim(_)), type text}, {"nombre", Text.Trim, type text}}),
    Faltantes = Table.Distinct(Table.SelectRows(Equipo,
        each not List.Contains(Ultimo[sigla_empresa], [sigla_empresa])), {"sigla_empresa"}),
    Todas = Table.Combine({Ultimo, Faltantes}),
    // Marca comercial y grupo (misma lista que sql/02_limpiar.sql)
    Marcas = #table({"sigla_empresa", "Marca", "Grupo"}, {
        {"AVA", "Avianca", "Grupo Avianca"}, {"AVR", "Avianca Express", "Grupo Avianca"},
        {"TPA", "Avianca Cargo", "Grupo Avianca"}, {"GLG", "Avianca Ecuador", "Grupo Avianca"},
        {"LRC", "Avianca Costa Rica", "Grupo Avianca"}, {"ARE", "LATAM Colombia", "Grupo LATAM"},
        {"LAE", "LATAM Cargo Colombia", "Grupo LATAM"}, {"LAN", "LATAM Airlines", "Grupo LATAM"},
        {"LPE", "LATAM Peru", "Grupo LATAM"}, {"RPB", "Wingo", "Wingo"}, {"VVC", "Viva Air", "Viva Air"},
        {"EFY", "EasyFly", "EasyFly"}, {"JEC", "JetSMART", "JetSMART"}, {"NSE", "Satena", "Satena"},
        {"ULS", "Ultra Air", "Ultra Air"}, {"CMP", "Copa Airlines", "Copa"},
        {"AAL", "American Airlines", "American Airlines"}, {"NKS", "Spirit Airlines", "Spirit Airlines"}}),
    Unido = Table.ExpandTableColumn(
        Table.NestedJoin(Todas, {"sigla_empresa"}, Marcas, {"sigla_empresa"}, "m", JoinKind.LeftOuter),
        "m", {"Marca", "Grupo"}),
    Nombres = Table.AddColumn(Unido, "Aerolínea", each if [Marca] = null then Text.Proper([nombre]) else [Marca], type text),
    Grupo = Table.AddColumn(Nombres, "Grupo empresarial", each if [Grupo] = null then [Aerolínea] else [Grupo], type text),
    // Para las gráficas: los grupos con marca propia y "Otras" para el resto
    GrupoTablero = Table.AddColumn(Grupo, "Grupo tablero", each if [Grupo] = null then "Otras" else [Grupo], type text),
    Final = Table.RenameColumns(Table.SelectColumns(GrupoTablero,
        {"sigla_empresa", "nombre", "Aerolínea", "Grupo empresarial", "Grupo tablero"}),
        {{"sigla_empresa", "Sigla"}, {"nombre", "Nombre reportado"}})
in
    Final
