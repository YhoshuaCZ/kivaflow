"""Dibujo básico del almacén con matplotlib: las 3 zonas de fondo, estaciones y pasillos."""
from matplotlib.collections import LineCollection

from kivaflow.config import CELDA_M, COLUMNAS, FILAS, ZONAS

COLOR_ZONA = {"Recepción y Almacenamiento": "#dbe7f5", "Picking": "#f7dede", "Empaque y Despacho": "#ddf0e3"}
COLOR_NIVEL = {"Baja": "#2b6cb0", "Media": "#dd6b20", "Alta": "#9b2c2c"}


def posiciones(nodos):
    return {k: (float(n["X_m"]), -float(n["Y_m"])) for k, n in nodos.items()}


def fondo(ax, nodos, pos, titulo=None, grilla=None):
    """Zonas como bandas de color, estaciones como cuadrados negros y, si se pasa
    `grilla` (lista de aristas), todos los pasillos en gris claro."""
    for nombre, cols in ZONAS:
        ax.axvspan(cols.start * CELDA_M - CELDA_M / 2, (cols.stop - 1) * CELDA_M + CELDA_M / 2,
                   color=COLOR_ZONA[nombre], zorder=0)
    if grilla:
        lineas(ax, pos, grilla, color="#d6d6d6", ancho=0.5, z=1)
    est = [pos[k] for k, n in nodos.items() if n["Tipo"] == "estacion"]
    ax.scatter(*zip(*est), s=14, c="black", marker="s", zorder=4)
    ax.set_xlim(-CELDA_M, COLUMNAS * CELDA_M)
    ax.set_ylim(-FILAS * CELDA_M, CELDA_M)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    if titulo:
        ax.set_title(titulo, fontsize=10)


def lineas(ax, pos, pares, color="black", ancho=1.0, z=2):
    """pares: [(u, v), ...] o [(u, v, algo), ...]; color: uno solo o una lista."""
    seg = [(pos[p[0]], pos[p[1]]) for p in pares]
    ax.add_collection(LineCollection(seg, colors=color, linewidths=ancho, zorder=z))


def recorrido(ax, pos, camino, color, ancho=2.5, etiqueta=None):
    xs, ys = zip(*(pos[n] for n in camino))
    ax.plot(xs, ys, color=color, linewidth=ancho, zorder=5, label=etiqueta)
    ax.scatter([xs[0]], [ys[0]], s=70, c=color, marker="o", zorder=6, edgecolors="black")
    ax.scatter([xs[-1]], [ys[-1]], s=110, c=color, marker="*", zorder=6, edgecolors="black")
