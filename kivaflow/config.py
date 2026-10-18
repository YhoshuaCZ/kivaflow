"""Parámetros del almacén. Todo el dataset sale de aquí y de la semilla."""

SEMILLA = 2026

# Cuadrícula: 45 filas x 40 columnas = 1800 ubicaciones (nodos).
FILAS = 45
COLUMNAS = 40

# Zonas funcionales por bandas de columnas (una por integrante del grupo).
# 13 + 14 + 13 columnas -> 585 + 630 + 585 nodos.
ZONAS = [
    ("Recepción y Almacenamiento", range(0, 13)),
    ("Picking", range(13, 27)),
    ("Empaque y Despacho", range(27, 40)),
]

# Separación entre ubicaciones vecinas, en metros (ancho de celda de la cuadrícula).
CELDA_M = 1.2

# Estaciones de trabajo: muelles de recepción (columna 0) y de despacho (última columna),
# una cada 5 filas. El resto de ubicaciones son racks.
FILAS_ESTACION = range(2, FILAS, 5)

# Velocidad media de un operario caminando, en m/s (la usada en el TB1).
VELOCIDAD_M_S = 1.1

# Congestión: cada arista recibe un nivel según cuántas rutas de picking la cruzan
# (terciles del tráfico simulado) y su distancia se multiplica por este factor.
FACTOR_CONGESTION = {"Baja": 1.0, "Media": 1.25, "Alta": 1.6}

# La congestión cambia con la hora. "punta" es la de FACTOR_CONGESTION (la que va en
# aristas.csv); en "valle" los pasillos concurridos se frenan menos.
PERFILES_HORA = {
    "punta": FACTOR_CONGESTION,
    "valle": {"Baja": 1.0, "Media": 1.1, "Alta": 1.25},
}

# Capacidad de cada pasillo para el flujo máximo: operarios por minuto que pueden
# cruzarlo. Un pasillo muy transitado deja menos capacidad libre.
CAPACIDAD_OPERARIOS_MIN = {"Baja": 3, "Media": 2, "Alta": 1}

# Pedidos simulados para medir el tráfico.
N_PEDIDOS = 2000
MAX_PRODUCTOS_POR_PEDIDO = 10
ZIPF_S = 1.0  # popularidad sintética: el producto de rango r se pide ~ 1 / r^s
