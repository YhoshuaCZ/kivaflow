"""Dibuja el grafo del almacén: nodos por zona y pasillos por nivel de congestión.

Uso: python scripts/dibujar_grafo.py   -> docs/grafo.png
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from kivaflow import grafo  # noqa: E402

COLOR_ZONA = {"Recepción y Almacenamiento": "#2b6cb0", "Picking": "#c53030", "Empaque y Despacho": "#2f855a"}
COLOR_NIVEL = {"Baja": "#cbd5e0", "Media": "#ed8936", "Alta": "#9b2c2c"}


def main():
    nodos = grafo.leer_nodos()
    aristas = grafo.leer_aristas()
    pos = {k: (float(n["X_m"]), -float(n["Y_m"])) for k, n in nodos.items()}

    fig, ax = plt.subplots(figsize=(12, 13))
    for nivel, color in COLOR_NIVEL.items():
        seg = [(pos[a["Nodo_Origen"]], pos[a["Nodo_Destino"]]) for a in aristas if a["Frecuencia_Pedidos"] == nivel]
        ax.add_collection(LineCollection(seg, colors=color, linewidths=0.6 if nivel == "Baja" else 1.4,
                                         label=f"Pasillo: congestión {nivel.lower()} ({len(seg)})"))
    for zona, color in COLOR_ZONA.items():
        xs = [pos[k] for k, n in nodos.items() if n["Zona"] == zona and n["Tipo"] == "rack"]
        ax.scatter(*zip(*xs), s=4, c=color, label=f"Rack · {zona}")
    est = [pos[k] for k, n in nodos.items() if n["Tipo"] == "estacion"]
    ax.scatter(*zip(*est), s=60, c="black", marker="s", label="Estación (muelle)")

    ax.set_title(f"KivaFlow · almacén {len(nodos)} nodos, {len(aristas)} aristas")
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_aspect("equal")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.05), ncol=2, fontsize=9)
    salida = RAIZ / "docs" / "grafo.png"
    salida.parent.mkdir(exist_ok=True)
    fig.savefig(salida, dpi=110, bbox_inches="tight")
    print(f"Escrito {salida}")


if __name__ == "__main__":
    main()
