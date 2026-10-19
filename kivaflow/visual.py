"""Figuras del almacén (matplotlib). Las usan los scripts y la app de Streamlit."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402

from . import paleta  # noqa: E402

COLOR_ZONA = paleta.ZONA
COLOR_NIVEL_FUERTE = paleta.CONGESTION
COLOR_NIVEL_SUAVE = {"Baja": "#EFEBE3", "Media": "#E8CF9C", "Alta": "#D9A496"}
plt.rcParams.update({"font.family": "serif", "axes.edgecolor": paleta.BORDE, "axes.labelcolor": paleta.SUAVE,
                     "xtick.color": paleta.SUAVE, "ytick.color": paleta.SUAVE, "figure.facecolor": paleta.PAPEL,
                     "axes.facecolor": paleta.TARJETA, "axes.titlesize": 13, "axes.titlecolor": paleta.TINTA})


def posiciones(nodos):
    return {k: (float(n["X_m"]), -float(n["Y_m"])) for k, n in nodos.items()}


def _pasillos(ax, aristas, pos, colores, etiquetas=True, anchos=(0.6, 1.4)):
    for nivel, color in colores.items():
        seg = [(pos[a["Nodo_Origen"]], pos[a["Nodo_Destino"]]) for a in aristas if a["Frecuencia_Pedidos"] == nivel]
        ax.add_collection(LineCollection(seg, colors=color, linewidths=anchos[0] if nivel == "Baja" else anchos[1],
                                         label=f"Congestión {nivel.lower()} ({len(seg)})" if etiquetas else None))


def _cerrar(fig, ax, titulo, ncol=2):
    ax.set_title(titulo)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_aspect("equal")
    ax.autoscale()
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.06), ncol=ncol, fontsize=9)
    fig.tight_layout()
    return fig


def almacen(nodos, aristas, tamano=(12, 13)):
    """Grafo completo: racks por zona, muelles y pasillos por congestión."""
    pos = posiciones(nodos)
    fig, ax = plt.subplots(figsize=tamano)
    _pasillos(ax, aristas, pos, COLOR_NIVEL_FUERTE)
    for zona, color in COLOR_ZONA.items():
        xs = [pos[k] for k, n in nodos.items() if n["Zona"] == zona and n["Tipo"] == "rack"]
        ax.scatter(*zip(*xs), s=4, c=color, label=f"Rack · {zona}")
    est = [pos[k] for k, n in nodos.items() if n["Tipo"] == "estacion"]
    ax.scatter(*zip(*est), s=60, c=paleta.TINTA, marker="s", label="Estación (muelle)")
    return _cerrar(fig, ax, f"Almacén: {len(nodos)} nodos, {len(aristas)} aristas")


def rutas(nodos, aristas, caminos, racks, muelle, titulo, tamano=(10, 11)):
    """caminos: {etiqueta: (lista_de_nodos, color, ancho)}."""
    pos = posiciones(nodos)
    fig, ax = plt.subplots(figsize=tamano)
    _pasillos(ax, aristas, pos, COLOR_NIVEL_SUAVE, anchos=(1.2, 1.2))
    for etiqueta, (camino, color, ancho) in caminos.items():
        xs, ys = zip(*(pos[n] for n in camino))
        ax.plot(xs, ys, color=color, lw=ancho, alpha=0.85, label=etiqueta)
    ax.scatter(*zip(*(pos[r] for r in racks)), s=120, c=paleta.ALGORITMO["edmonds_karp"], zorder=5, label="Racks del pedido")
    ax.scatter(*pos[muelle], s=180, c=paleta.TINTA, marker="s", zorder=5, label="Muelle de inicio")
    return _cerrar(fig, ax, titulo)


def corte(nodos, aristas, cuellos, lado_fuente, titulo, tamano=(10, 11)):
    pos = posiciones(nodos)
    fig, ax = plt.subplots(figsize=tamano)
    ax.add_collection(LineCollection([(pos[a["Nodo_Origen"]], pos[a["Nodo_Destino"]]) for a in aristas],
                                     colors="#EFEBE3", linewidths=1))
    ax.add_collection(LineCollection([(pos[u], pos[v]) for u, v, _ in cuellos], colors=paleta.ALGORITMO["edmonds_karp"], linewidths=3,
                                     label=f"Corte mínimo: {len(cuellos)} pasillos saturados"))
    lado = [pos[n] for n in lado_fuente if n in pos]
    if lado:
        ax.scatter(*zip(*lado), s=3, c=paleta.ZONA["Recepción y Almacenamiento"], label="Lado de la fuente del corte")
    return _cerrar(fig, ax, titulo)
