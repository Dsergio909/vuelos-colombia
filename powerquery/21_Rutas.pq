// Dimensión de rutas: cada par de aeropuertos sin dirección y su tráfico, con su nombre para mostrar.
// La clave es "Clave ruta" (ruta + tráfico): IDA es Puerto Inírida en una ruta nacional e Idaho en una internacional.
let
    // Primero las combinaciones distintas con sus pasajeros (unas 10.000, no medio millón de filas)
    Base = Table.Group(Trafico, {"Clave ruta", "Ruta", "Origen", "Destino", "Clave origen", "Clave destino", "Tráfico"},
        {{"Pasajeros", each List.Sum([Pasajeros]), Int64.Type}}),
    ClaveA = Table.AddColumn(Base, "Clave A", each if [Origen] < [Destino] then [Clave origen] else [Clave destino], type text),
    ClaveB = Table.AddColumn(ClaveA, "Clave B", each if [Origen] < [Destino] then [Clave destino] else [Clave origen], type text),
    // Si una ruta trae dos nombres (un país escrito de dos formas), gana el de más pasajeros (igual que en el SQL)
    Pares = Table.Group(ClaveB, {"Clave ruta", "Ruta", "Clave A", "Clave B", "Tráfico"},
        {{"Pasajeros", each List.Sum([Pasajeros]), Int64.Type}}),
    Unicas = Table.Group(Pares, {"Clave ruta"}, {{"fila", each Table.Max(_, "Pasajeros"), type record}}),
    Expandida = Table.FromRecords(Unicas[fila]),
    Unicas2 = Table.SelectColumns(Expandida, {"Clave ruta", "Ruta", "Clave A", "Clave B", "Tráfico"}),
    // Aeropuertos se guarda en memoria para no calcularla dos veces
    Aero = Table.Buffer(Table.SelectColumns(Aeropuertos, {"Clave", "Ciudad aeropuerto"})),
    UneA = Table.ExpandTableColumn(Table.NestedJoin(Unicas2, {"Clave A"}, Aero, {"Clave"}, "a", JoinKind.LeftOuter),
        "a", {"Ciudad aeropuerto"}, {"Ciudad A"}),
    UneB = Table.ExpandTableColumn(Table.NestedJoin(UneA, {"Clave B"}, Aero, {"Clave"}, "b", JoinKind.LeftOuter),
        "b", {"Ciudad aeropuerto"}, {"Ciudad B"}),
    Nombre = Table.AddColumn(UneB, "Nombre ruta", each [Ciudad A] & " - " & [Ciudad B], type text),
    Final = Table.RenameColumns(Table.SelectColumns(Nombre, {"Clave ruta", "Ruta", "Nombre ruta", "Ciudad A", "Ciudad B", "Tráfico"}),
        {{"Tráfico", "Tráfico de la ruta"}})
in
    Final
