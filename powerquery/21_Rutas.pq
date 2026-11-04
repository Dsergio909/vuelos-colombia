// Dimensión de rutas: cada par de aeropuertos sin dirección, con su nombre para mostrar.
let
    Base = Table.SelectColumns(Trafico, {"Ruta", "Origen", "Destino", "Clave origen", "Clave destino", "Tráfico"}),
    Extremos = Table.AddColumn(Base, "Claves", each if [Origen] < [Destino]
        then {[Clave origen], [Clave destino]} else {[Clave destino], [Clave origen]}),
    Unicas = Table.Distinct(Table.SelectColumns(Extremos, {"Ruta", "Claves", "Tráfico"}), {"Ruta"}),
    A = Table.AddColumn(Unicas, "Clave A", each [Claves]{0}, type text),
    B = Table.AddColumn(A, "Clave B", each [Claves]{1}, type text),
    UneA = Table.ExpandTableColumn(Table.NestedJoin(B, {"Clave A"}, Aeropuertos, {"Clave"}, "a", JoinKind.LeftOuter),
        "a", {"Ciudad aeropuerto"}, {"Ciudad A"}),
    UneB = Table.ExpandTableColumn(Table.NestedJoin(UneA, {"Clave B"}, Aeropuertos, {"Clave"}, "b", JoinKind.LeftOuter),
        "b", {"Ciudad aeropuerto"}, {"Ciudad B"}),
    Nombre = Table.AddColumn(UneB, "Nombre ruta", each [Ciudad A] & " - " & [Ciudad B], type text),
    Final = Table.RenameColumns(Table.SelectColumns(Nombre, {"Ruta", "Nombre ruta", "Ciudad A", "Ciudad B", "Tráfico"}),
        {{"Tráfico", "Tráfico de la ruta"}})
in
    Final
