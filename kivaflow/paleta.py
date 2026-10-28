"""Paleta «Centro de control»: un solo lugar para los colores de figuras y app.

Tema oscuro al estilo de los visualizadores de algoritmos (VisuAlgo, Algorithm
Visualizer, Pathfinding Visualizer) y de los tableros de control de almacenes:
fondo grafito, un acento por algoritmo, amarillo para lo que se procesa ahora y
una escala de gris a rojo para la congestión.
"""

PAPEL = "#0D1117"        # fondo
TARJETA = "#161B22"      # paneles y lienzo de las figuras
BORDE = "#30363D"
TINTA = "#E6EDF3"        # texto
SUAVE = "#8B949E"        # texto secundario
REJILLA = "#21262D"
ACENTO = "#2F81F7"       # botones y enlaces activos

ALGORITMO = {
    "bfs": "#38BDF8",           # celeste
    "bellman_ford": "#A78BFA",  # violeta
    "edmonds_karp": "#F472B6",  # rosa
}
ALGORITMO_CLARO = {"bfs": "#1D5B7E", "bellman_ford": "#4C3F8F", "edmonds_karp": "#7A2F57"}  # nodos visitados
FRENTE = "#FACC15"       # lo que se está procesando ahora (amarillo)
INICIO = "#22C55E"       # punto de partida (verde)
DESTINO = "#F87171"      # destinos (rojo)
EXITO = "#3FB950"

CONGESTION = {"Baja": "#3A424D", "Media": "#F59E0B", "Alta": "#EF4444"}
CONGESTION_SUAVE = {"Baja": "#262C35", "Media": "#5A4317", "Alta": "#5E2626"}  # de fondo, bajo las animaciones
ZONA = {  # tonos apagados: la zona es contexto, no protagonista
    "Recepción y Almacenamiento": "#6E8BC0",
    "Picking": "#B9975B",
    "Empaque y Despacho": "#6FAE88",
}
CALOR = [[0, "#1F2630"], [0.5, "#F59E0B"], [1, "#EF4444"]]   # escala para cruces

SANS = "Inter, system-ui, sans-serif"
MONO = "JetBrains Mono, Consolas, monospace"
