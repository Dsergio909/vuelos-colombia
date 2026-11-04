// Dimensión de rutas: cada par de aeropuertos sin dirección, con su nombre para mostrar.
let
    // Primero las combinaciones distintas (unas 10.000, no medio millón de filas)
    Base = Table.Distinct(Table.SelectColumns(Trafico, {"Ruta", "Origen", "Destino", "Clave origen", "Clave destino", "Tráfico"})),
    ClaveA = Table.AddColumn(Base, "Clave A", each if [Origen] < [Destino] then [Clave origen] else [Clave destino], type text),
    ClaveB = Table.AddColumn(ClaveA, "Clave B", each if [Origen] < [Destino] then [Clave destino] else [Clave origen], type text),
    Unicas = Table.Distinct(Table.SelectColumns(ClaveB, {"Ruta", "Clave A", "Clave B", "Tráfico"}), {"Ruta"}),
    // Aeropuertos se guarda en memoria para no calcularla dos veces
    Aero = Table.Buffer(Table.SelectColumns(Aeropuertos, {"Clave", "Ciudad aeropuerto"})),
    UneA = Table.ExpandTableColumn(Table.NestedJoin(Unicas, {"Clave A"}, Aero, {"Clave"}, "a", JoinKind.LeftOuter),
        "a", {"Ciudad aeropuerto"}, {"Ciudad A"}),
    UneB = Table.ExpandTableColumn(Table.NestedJoin(UneA, {"Clave B"}, Aero, {"Clave"}, "b", JoinKind.LeftOuter),
        "b", {"Ciudad aeropuerto"}, {"Ciudad B"}),
    Nombre = Table.AddColumn(UneB, "Nombre ruta", each [Ciudad A] & " - " & [Ciudad B], type text),
    Final = Table.RenameColumns(Table.SelectColumns(Nombre, {"Ruta", "Nombre ruta", "Ciudad A", "Ciudad B", "Tráfico"}),
        {{"Tráfico", "Tráfico de la ruta"}})
in
    Final
