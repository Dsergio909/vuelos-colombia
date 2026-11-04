// Calendario mensual: del primer al último mes que traen los datos.
let
    Fin = List.Max(Trafico[Fecha]),
    Meses = List.Generate(() => #date(2020, 1, 1), each _ <= Fin, each Date.AddMonths(_, 1)),
    Tabla = Table.FromList(Meses, Splitter.SplitByNothing(), type table [Fecha = date]),
    Año = Table.AddColumn(Tabla, "Año", each Date.Year([Fecha]), Int64.Type),
    Mes = Table.AddColumn(Año, "Mes", each Date.Month([Fecha]), Int64.Type),
    NombreMes = Table.AddColumn(Mes, "Nombre mes",
        each {"ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"}{[Mes] - 1}, type text),
    NombreLargo = Table.AddColumn(NombreMes, "Mes largo",
        each {"enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
              "octubre", "noviembre", "diciembre"}{[Mes] - 1}, type text)
in
    NombreLargo
