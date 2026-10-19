"""Paleta «Papel y tinta»: un solo lugar para los colores de figuras y app.

El color solo se usa donde significa algo: un tono por algoritmo y una escala
de beige a ladrillo para la congestión. Todo lo demás es tinta sobre papel.
"""

PAPEL = "#F7F5F0"        # fondo
TARJETA = "#FFFFFF"
BORDE = "#E7E2D8"
TINTA = "#1F2328"        # texto
SUAVE = "#6B6B6B"        # texto secundario
REJILLA = "#EDE9E1"

ALGORITMO = {
    "bfs": "#2F4B8A",           # azul tinta
    "bellman_ford": "#2E6B4F",  # verde pino
    "edmonds_karp": "#A2412E",  # ladrillo
}
ALGORITMO_CLARO = {"bfs": "#C9D3EA", "bellman_ford": "#C7DDD1", "edmonds_karp": "#EBCFC6"}
FRENTE = "#D6A54A"       # lo que se está procesando ahora (ocre)

CONGESTION = {"Baja": "#E9E4D8", "Media": "#D6A54A", "Alta": "#A2412E"}
ZONA = {  # tonos apagados: la zona es contexto, no protagonista
    "Recepción y Almacenamiento": "#8E9BB3",
    "Picking": "#B8A27C",
    "Empaque y Despacho": "#8FA394",
}
CALOR = [[0, "#F3EEE3"], [0.5, "#D6A54A"], [1, "#A2412E"]]   # escala para cruces

SERIF = "Newsreader, Georgia, serif"
SANS = "Inter, system-ui, sans-serif"
MONO = "JetBrains Mono, Consolas, monospace"
