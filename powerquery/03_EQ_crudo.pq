// Tráfico por Equipo tal como viene de Aerocivil (todo texto). No se carga al modelo.
let
    Origen = Parquet.Document(File.Contents(CarpetaDatos & "\fuente\equipo.parquet"))
in
    Origen
