"""Demostración del MST (Kruskal y Prim) sobre el mapa de 3 zonas del almacén.

Uso:
    python scripts/demo_mst.py              # imprime el detalle y guarda 2 figuras en resultados/
    python scripts/demo_mst.py --animar     # además abre una ventana con el árbol creciendo
    python scripts/demo_mst.py --ejemplo    # además muestra Kruskal paso a paso en un grafo de 5 nodos

Solo usa matplotlib (y el código propio de kivaflow/mst.py).
"""
import argparse
import sys
import time
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from kivaflow import grafo  # noqa: E402
from kivaflow.config import CELDA_M, COLUMNAS, FILAS, ZONAS  # noqa: E402
from kivaflow.mst import kruskal, lista_aristas, prim  # noqa: E402

COLOR_ZONA = {"Recepción y Almacenamiento": "#dbe7f5", "Picking": "#f7dede", "Empaque y Despacho": "#ddf0e3"}
COLOR_NIVEL = {"Baja": "#2b6cb0", "Media": "#dd6b20", "Alta": "#9b2c2c"}
ETAPAS = (0.10, 0.25, 0.50, 1.00)


def cargar():
    nodos = grafo.leer_nodos()
    filas = grafo.leer_aristas()
    nivel = {}
    for a in filas:
        nivel[(a["Nodo_Origen"], a["Nodo_Destino"])] = a["Frecuencia_Pedidos"]
        nivel[(a["Nodo_Destino"], a["Nodo_Origen"])] = a["Frecuencia_Pedidos"]
    pos = {k: (float(n["X_m"]), -float(n["Y_m"])) for k, n in nodos.items()}
    return nodos, filas, lista_aristas(filas), nivel, pos


def medir(funcion, *args):
    t0 = time.perf_counter()
    r = funcion(*args)
    return r, (time.perf_counter() - t0) * 1000


def imprimir_detalle(nodos, aristas, nivel, resultados):
    total = sum(w for *_, w in aristas)
    print(f"\nAlmacén: V = {len(nodos)} ubicaciones, E = {len(aristas)} pasillos")
    print(f"Peso: Distancia_Ajustada_m (1,2 / 1,5 / 1,92 m según congestión Baja / Media / Alta)")
    print(f"Todos los pasillos suman {total:,.2f} m ajustados\n")
    print(f"{'':<26}{'Kruskal':>14}{'Prim':>14}")
    k, p = resultados
    filas = [
        ("Costo total (m ajustados)", f"{k[0].costo:,.2f}", f"{p[0].costo:,.2f}"),
        ("Pasillos en el árbol", len(k[0].aristas), len(p[0].aristas)),
        ("Aristas revisadas", k[0].revisadas, p[0].revisadas),
        ("Descartadas (ciclo / viejas)", k[0].descartadas, p[0].descartadas),
        ("Tiempo (ms)", f"{k[1]:.1f}", f"{p[1]:.1f}"),
    ]
    for etiqueta, a, b in filas:
        print(f"{etiqueta:<26}{a:>14}{b:>14}")

    print("\nPasillos del árbol por congestión (vs. todo el almacén):")
    en_grafo = Counter(nivel[(u, v)] for u, v, _ in aristas)
    for r, _ in resultados:
        c = Counter(nivel[(u, v)] for u, v, _ in r.aristas)
        print(f"  {r.algoritmo:<8}" + "  ".join(f"{n}: {c[n]:>4} de {en_grafo[n]}" for n in ("Baja", "Media", "Alta")))

    mismos = {frozenset((u, v)) for u, v, _ in k[0].aristas} & {frozenset((u, v)) for u, v, _ in p[0].aristas}
    print(f"\nMismo costo: {abs(k[0].costo - p[0].costo) < 1e-6}. "
          f"Pasillos en común: {len(mismos)} de {len(k[0].aristas)}. "
          "Con solo 3 pesos distintos hay empates, así que puede haber varios MST del mismo costo.")
    print(f"La red de servicio usa el {100 * k[0].costo / total:.1f} % del costo de todos los pasillos.\n")


def fondo(ax, pos, nodos):
    """Las 3 zonas como bandas de color, y las estaciones como cuadrados."""
    for nombre, cols in ZONAS:
        ax.axvspan(cols.start * CELDA_M - CELDA_M / 2, (cols.stop - 1) * CELDA_M + CELDA_M / 2,
                   color=COLOR_ZONA[nombre], zorder=0)
    est = [pos[k] for k, n in nodos.items() if n["Tipo"] == "estacion"]
    ax.scatter(*zip(*est), s=14, c="black", marker="s", zorder=3)
    ax.set_xlim(-CELDA_M, COLUMNAS * CELDA_M)
    ax.set_ylim(-FILAS * CELDA_M, CELDA_M)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])


def dibujar_aristas(ax, pos, aristas, nivel, ancho=1.0):
    from matplotlib.collections import LineCollection
    seg = [(pos[u], pos[v]) for u, v, _ in aristas]
    col = [COLOR_NIVEL[nivel[(u, v)]] for u, v, _ in aristas]
    ax.add_collection(LineCollection(seg, colors=col, linewidths=ancho, zorder=2))


def figura_etapas(plt, nodos, pos, nivel, resultados, salida):
    """Cómo crece el árbol: Kruskal arma un bosque disperso; Prim, un solo árbol."""
    fig, axs = plt.subplots(2, len(ETAPAS), figsize=(4 * len(ETAPAS), 10))
    for fila, (r, _) in enumerate(resultados):
        for col, frac in enumerate(ETAPAS):
            ax = axs[fila][col]
            fondo(ax, pos, nodos)
            n = round(frac * len(r.aristas))
            dibujar_aristas(ax, pos, r.aristas[:n], nivel)
            ax.set_title(f"{r.algoritmo}: {n} de {len(r.aristas)} pasillos\n"
                         f"costo parcial {sum(w for *_, w in r.aristas[:n]):,.1f}", fontsize=10)
    fig.suptitle("Kruskal arma varios pedazos (bosque) y los une; Prim crece como una sola mancha desde una esquina",
                 fontsize=12)
    fig.savefig(salida, dpi=100, bbox_inches="tight")
    plt.close(fig)


def figura_red(plt, nodos, pos, nivel, r, salida):
    fig, ax = plt.subplots(figsize=(10, 11))
    fondo(ax, pos, nodos)
    dibujar_aristas(ax, pos, r.aristas, nivel, ancho=1.6)
    c = Counter(nivel[(u, v)] for u, v, _ in r.aristas)
    from matplotlib.patches import Patch
    leyenda = [Patch(color=COLOR_NIVEL[n], label=f"Pasillo de congestión {n.lower()} ({c[n]})") for n in COLOR_NIVEL]
    leyenda += [Patch(color=COLOR_ZONA[z], label=z) for z in COLOR_ZONA]
    ax.legend(handles=leyenda, loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=2, fontsize=9)
    ax.set_title(f"Red de servicio (MST con {r.algoritmo}): {len(r.aristas)} pasillos, "
                 f"{r.costo:,.2f} m ajustados")
    fig.savefig(salida, dpi=110, bbox_inches="tight")
    plt.close(fig)


def animar(plt, nodos, pos, nivel, resultados, paso=15):
    from matplotlib.animation import FuncAnimation
    from matplotlib.collections import LineCollection
    fig, axs = plt.subplots(1, 2, figsize=(13, 7.5))
    lineas = []
    for ax, (r, _) in zip(axs, resultados):
        fondo(ax, pos, nodos)
        lc = LineCollection([], linewidths=1.4, zorder=2)
        ax.add_collection(lc)
        lineas.append(lc)
    total = max(len(r.aristas) for r, _ in resultados)

    def cuadro(i):
        n = min((i + 1) * paso, total)
        for ax, lc, (r, _) in zip(axs, lineas, resultados):
            sub = r.aristas[:n]
            lc.set_segments([(pos[u], pos[v]) for u, v, _ in sub])
            lc.set_color([COLOR_NIVEL[nivel[(u, v)]] for u, v, _ in sub])
            ax.set_title(f"{r.algoritmo}: {len(sub)} pasillos · costo {sum(w for *_, w in sub):,.1f}")
        return lineas

    anim = FuncAnimation(fig, cuadro, frames=-(-total // paso), interval=40, repeat=False)
    plt.show()
    return anim


def ejemplo_a_mano():
    """Kruskal paso a paso en el grafo chico de los tests, para explicarlo en la sustentación."""
    from kivaflow.ufds import UFDS
    nodos = list("ABCDE")
    aristas = [("A", "B", 1), ("B", "C", 2), ("A", "C", 3), ("C", "D", 4),
               ("B", "D", 5), ("D", "E", 6), ("C", "E", 7)]
    print("Ejemplo a mano: Kruskal en 5 nodos (aristas ya ordenadas por peso)")
    print(f"{'Arista':<8}{'Peso':>5}  {'¿buscar(u) = buscar(v)?':<26}Decisión          Grupos")
    uf, costo = UFDS(nodos), 0
    for u, v, w in sorted(aristas, key=lambda a: a[2]):
        mismo = uf.buscar(u) == uf.buscar(v)
        if not mismo:
            uf.unir(u, v)
            costo += w
        grupos = {}
        for n in nodos:
            grupos.setdefault(uf.buscar(n), []).append(n)
        print(f"{u}-{v:<6}{w:>5}  {'sí' if mismo else 'no':<26}{'descartar (ciclo)' if mismo else 'agregar':<18}"
              + " ".join("{" + ",".join(g) + "}" for g in grupos.values()))
        if uf.grupos == 1:
            break
    print(f"Costo del MST: {costo}\n")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--animar", action="store_true", help="abrir una ventana con el árbol creciendo")
    p.add_argument("--ejemplo", action="store_true", help="Kruskal paso a paso en un grafo de 5 nodos")
    args = p.parse_args()

    import matplotlib
    if not args.animar:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    if args.ejemplo:
        ejemplo_a_mano()
    nodos, _, aristas, nivel, pos = cargar()
    resultados = [medir(kruskal, list(nodos), aristas), medir(prim, list(nodos), aristas)]
    imprimir_detalle(nodos, aristas, nivel, resultados)

    salida = RAIZ / "resultados"
    salida.mkdir(exist_ok=True)
    figura_etapas(plt, nodos, pos, nivel, resultados, salida / "mst_etapas.png")
    figura_red(plt, nodos, pos, nivel, resultados[0][0], salida / "mst_red_servicio.png")
    print(f"Figuras: {salida / 'mst_etapas.png'} y {salida / 'mst_red_servicio.png'}")
    if args.animar:
        animar(plt, nodos, pos, nivel, resultados)


if __name__ == "__main__":
    main()
