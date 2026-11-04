// Función: pasa a mayúsculas, quita espacios de los extremos y quita tildes.
// "Montería " y "MONTERIA" quedan iguales: "MONTERIA". Hace lo mismo que strip_accents de DuckDB.
(texto as nullable text) as nullable text =>
    if texto = null then null
    else
        let
            Pares = {
                {"Á", "A"}, {"É", "E"}, {"Í", "I"}, {"Ó", "O"}, {"Ú", "U"}, {"Ü", "U"}, {"Ñ", "N"},
                {"À", "A"}, {"È", "E"}, {"Ì", "I"}, {"Ò", "O"}, {"Ù", "U"},
                {"Â", "A"}, {"Ê", "E"}, {"Î", "I"}, {"Ô", "O"}, {"Û", "U"},
                {"Ã", "A"}, {"Õ", "O"}, {"Ç", "C"}, {"Ä", "A"}, {"Ë", "E"}, {"Ï", "I"}, {"Ö", "O"}
            },
            Mayusculas = Text.Upper(Text.Trim(texto)),
            SinTildes = List.Accumulate(Pares, Mayusculas, (t, par) => Text.Replace(t, par{0}, par{1}))
        in
            SinTildes
