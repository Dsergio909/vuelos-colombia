// Dimensión de aeropuertos: un código + país, con su ciudad y sus coordenadas.
// El mismo aeropuerto aparece como "CALI" y "SANTIAGO DE CALI": se toma el nombre más usado.
let
    Base = Table.SelectRows(OD_crudo, each ([tr_fico_n_i] = "N" or [tr_fico_n_i] = "I")
        and (fnQuitarTildes([pais_origen]) = "COLOMBIA" or fnQuitarTildes([pais_destino]) = "COLOMBIA")),
    Origenes = Table.RenameColumns(Table.SelectColumns(Base, {"origen", "pais_origen", "ciudad_origen"}),
        {{"origen", "Código"}, {"pais_origen", "País"}, {"ciudad_origen", "Ciudad"}}),
    Destinos = Table.RenameColumns(Table.SelectColumns(Base, {"destino", "pais_destino", "ciudad_destino"}),
        {{"destino", "Código"}, {"pais_destino", "País"}, {"ciudad_destino", "Ciudad"}}),
    Todos = Table.Combine({Origenes, Destinos}),
    Limpios = Table.TransformColumns(Todos, {{"Código", each Text.Upper(Text.Trim(_)), type text},
        {"País", fnQuitarTildes, type text}, {"Ciudad", fnQuitarTildes, type text}}),
    Conteo = Table.Group(Limpios, {"Código", "País", "Ciudad"}, {{"Filas", each Table.RowCount(_), Int64.Type}}),
    // El nombre más usado; si empatan, el primero en orden alfabético (igual que en SQL)
    Ordenado = Table.Buffer(Table.Sort(Conteo, {{"Código", Order.Ascending}, {"País", Order.Ascending},
        {"Filas", Order.Descending}, {"Ciudad", Order.Ascending}})),
    Moda = Table.Distinct(Ordenado, {"Código", "País"}),
    // Nombres oficiales largos a la forma corta (misma lista que sql/02_limpiar.sql)
    Corta = [#"BOGOTA, D.C." = "BOGOTA", #"SANTIAGO DE CALI" = "CALI", #"SAN JOSE DE CUCUTA" = "CUCUTA",
        #"CARTAGENA DE INDIAS" = "CARTAGENA", #"RIONEGRO - ANTIOQUIA" = "RIONEGRO", #"SAN ANDRES - ISLA" = "SAN ANDRES",
        #"SAN ANDRES DE TUMACO" = "TUMACO", #"EL YOPAL" = "YOPAL", MEXICO = "CIUDAD DE MEXICO", TIGUANA = "TIJUANA",
        DALAS = "DALLAS", EZEIZA = "BUENOS AIRES", INIRIDA = "PUERTO INIRIDA"],
    CiudadCorta = Table.TransformColumns(Moda, {{"Ciudad", each Record.FieldOrDefault(Corta, _, _), type text}}),
    Etiqueta = Table.AddColumn(CiudadCorta, "Etiqueta",
        each if [Código] = "MDE" then "MEDELLIN (RIONEGRO)"
             else if [Código] = "EOH" then "MEDELLIN (OLAYA HERRERA)" else [Ciudad], type text),
    // Para mostrar: tildes de vuelta en las ciudades más grandes y el resto en tipo título
    ConTildes = [BOGOTA = "Bogotá", #"MEDELLIN (RIONEGRO)" = "Medellín (Rionegro)",
        #"MEDELLIN (OLAYA HERRERA)" = "Medellín (Olaya Herrera)", CUCUTA = "Cúcuta", MONTERIA = "Montería",
        #"SAN ANDRES" = "San Andrés", QUIBDO = "Quibdó", POPAYAN = "Popayán", IBAGUE = "Ibagué",
        #"CIUDAD DE MEXICO" = "Ciudad de México", PANAMA = "Panamá", #"SAO PAULO" = "São Paulo", CANCUN = "Cancún",
        #"NEW YORK" = "Nueva York", #"PUERTO INIRIDA" = "Puerto Inírida", #"PUERTO ASIS" = "Puerto Asís",
        #"SAN JOSE DEL GUAVIARE" = "San José del Guaviare", MITU = "Mitú", APARTADO = "Apartadó"],
    Mostrar = Table.AddColumn(Etiqueta, "Ciudad aeropuerto",
        each Record.FieldOrDefault(ConTildes, [Etiqueta], Text.Proper([Etiqueta])), type text),
    Clave = Table.AddColumn(Mostrar, "Clave", each [Código] & "|" & [País], type text),
    // Coordenadas de OurAirports (dominio público), armadas con scripts/coordenadas_aeropuertos.py
    Csv = Csv.Document(File.Contents(CarpetaDatos & "\referencia\aeropuertos_coordenadas.csv"),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Coordenadas = Table.TransformColumnTypes(Table.PromoteHeaders(Csv, [PromoteAllScalars = true]),
        {{"latitud", type number}, {"longitud", type number}}, "en-US"),
    Unido = Table.NestedJoin(Clave, {"Código", "País"}, Coordenadas, {"codigo", "pais"}, "c", JoinKind.LeftOuter),
    ConCoordenadas = Table.ExpandTableColumn(Unido, "c", {"latitud", "longitud"}, {"Latitud", "Longitud"}),
    Final = Table.SelectColumns(ConCoordenadas, {"Clave", "Código", "País", "Ciudad aeropuerto", "Latitud", "Longitud"})
in
    Final
