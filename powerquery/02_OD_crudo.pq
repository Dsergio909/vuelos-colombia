// Tráfico Origen-Destino tal como viene de Aerocivil (todo texto). No se carga al modelo.
let
    Origen = Parquet.Document(File.Contents(CarpetaDatos & "\fuente\origen_destino.parquet"))
in
    Origen
