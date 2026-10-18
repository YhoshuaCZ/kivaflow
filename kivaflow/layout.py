"""Geometría del almacén: nodos (ubicaciones) y aristas (pasillos entre vecinos)."""
from dataclasses import dataclass

from . import config


def id_nodo(fila, col):
    return f"{fila:02d}-{col:02d}"


def zona_de(col):
    for nombre, columnas in config.ZONAS:
        if col in columnas:
            return nombre
    raise ValueError(f"columna fuera del almacén: {col}")


@dataclass
class Nodo:
    id: str
    fila: int
    col: int
    x_m: float
    y_m: float
    zona: str
    tipo: str          # "rack" o "estacion"
    sku: str = ""      # SKU principal (solo racks), se asigna después


@dataclass
class Arista:
    origen: str
    destino: str
    pasillo: str       # H<fila> si es horizontal, V<col> si es vertical
    distancia_m: float


def construir_nodos():
    nodos = []
    for fila in range(config.FILAS):
        for col in range(config.COLUMNAS):
            es_muelle = col in (0, config.COLUMNAS - 1) and fila in config.FILAS_ESTACION
            nodos.append(Nodo(
                id=id_nodo(fila, col), fila=fila, col=col,
                x_m=round(col * config.CELDA_M, 2), y_m=round(fila * config.CELDA_M, 2),
                zona=zona_de(col), tipo="estacion" if es_muelle else "rack",
            ))
    return nodos


def construir_aristas():
    """Cada ubicación se conecta con la de la derecha y la de abajo (cuadrícula 4-vecinos).

    Total: FILAS*(COLUMNAS-1) + COLUMNAS*(FILAS-1) = 45*39 + 40*44 = 3515 aristas.
    """
    aristas = []
    for fila in range(config.FILAS):
        for col in range(config.COLUMNAS):
            if col + 1 < config.COLUMNAS:
                aristas.append(Arista(id_nodo(fila, col), id_nodo(fila, col + 1), f"H{fila:02d}", config.CELDA_M))
            if fila + 1 < config.FILAS:
                aristas.append(Arista(id_nodo(fila, col), id_nodo(fila + 1, col), f"V{col:02d}", config.CELDA_M))
    return aristas
