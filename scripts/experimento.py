"""Experimento con muchos pedidos: cuánto tiempo de caminata ahorra cada decisión.

El aplicativo compara un pedido a la vez. Aquí se repite con pedidos al azar de 2, 4,
6 y 8 productos (elegidos según su popularidad, cada uno saliendo de un muelle de
Despacho al azar) y se promedian tres estrategias:

    BFS + orden voraz            ruta con menos pasillos; no ve la congestión
    Bellman-Ford + orden voraz   ruta de menor distancia ajustada por congestión
    Bellman-Ford + orden óptimo  además elige el mejor orden de visita (Held-Karp)

Uso:
    python scripts/experimento.py                 # 40 pedidos por tamaño + tabla y gráfica (unos 4 minutos)
    python scripts/experimento.py --pedidos 10    # más rápido (para probar)
    python scripts/experimento.py --sin-ventana   # solo guarda los archivos
"""
import argparse
import csv
import random
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

from kivaflow import config  # noqa: E402

SALIDA = RAIZ / "resultados"
TAMANOS = (2, 4, 6, 8)
ESTRATEGIAS = [("BFS + voraz", "BFS", "voraz", "#718096"),
               ("Bellman-Ford + voraz", "Bellman-Ford", "voraz", "#dd6b20"),
               ("Bellman-Ford + óptimo", "Bellman-Ford", "óptimo", "#2f855a")]


def correr(a, n_pedidos, semilla=config.SEMILLA):
    """Una fila por pedido y estrategia. Determinista: los pedidos salen de la semilla."""
    rng = random.Random(semilla)
    filas = []
    for k in TAMANOS:
        for i in range(n_pedidos):
            origen = rng.choice(a.muelles_despacho)
            productos = a.pedido_al_azar(k, semilla=rng.random())
            for nombre, algoritmo, orden, _ in ESTRATEGIAS:
                m, _ = a.ruta(algoritmo, origen, productos, a_despacho=True, orden=orden, repeticiones=1)
                filas.append({"Productos": k, "Pedido": i, "Origen": origen, "Estrategia": nombre,
                              "Pasillos": m.resultado["pasillos recorridos"],
                              "Metros_ajustados": float(m.resultado["metros ajustados"][:-2]),
                              "Tiempo_operario_s": round(float(m.resultado["metros ajustados"][:-2])
                                                         / config.VELOCIDAD_M_S, 1),
                              "Calculo_ms": round(m.ms, 2)})
        print(f"{k} productos: {n_pedidos} pedidos listos", flush=True)
    return filas


def resumir(filas):
    """Promedios por tamaño de pedido: [{Productos, <estrategia>: s, ahorros…}]."""
    tabla = []
    for k in TAMANOS:
        fila = {"Productos": k}
        for nombre, *_ in ESTRATEGIAS:
            sel = [f for f in filas if f["Productos"] == k and f["Estrategia"] == nombre]
            fila[nombre] = sum(f["Tiempo_operario_s"] for f in sel) / len(sel)
            fila[nombre + " ms"] = sum(f["Calculo_ms"] for f in sel) / len(sel)
        voraz = {f["Pedido"]: f["Metros_ajustados"] for f in filas
                 if f["Productos"] == k and f["Estrategia"] == "Bellman-Ford + voraz"}
        optimo = {f["Pedido"]: f["Metros_ajustados"] for f in filas
                  if f["Productos"] == k and f["Estrategia"] == "Bellman-Ford + óptimo"}
        fila["voraz ya óptimo"] = sum(voraz[p] - optimo[p] < 0.005 for p in voraz) / len(voraz)
        tabla.append(fila)
    return tabla


def main():
    from app import Almacen
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pedidos", type=int, default=40, help="pedidos por tamaño (por defecto 40)")
    p.add_argument("--sin-ventana", action="store_true", help="solo guardar los archivos, sin abrir la gráfica")
    args = p.parse_args()
    import matplotlib
    if args.sin_ventana:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    filas = correr(Almacen(), args.pedidos)
    SALIDA.mkdir(exist_ok=True)
    with open(SALIDA / "experimento_pedidos.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(filas)

    tabla = resumir(filas)
    bfs, bf, opt = (e[0] for e in ESTRATEGIAS)
    print(f"\nTiempo medio de caminata del operario (s), {args.pedidos} pedidos por tamaño:")
    print(f"{'Productos':>9}{bfs:>14}{'B-F + voraz':>14}{'B-F + óptimo':>14}{'Ahorro B-F':>12}"
          f"{'Ahorro óptimo':>15}{'Voraz ya óptimo':>17}")
    for t in tabla:
        print(f"{t['Productos']:>9}{t[bfs]:>14.1f}{t[bf]:>14.1f}{t[opt]:>14.1f}"
              f"{100 * (1 - t[bf] / t[bfs]):>11.1f}%{100 * (1 - t[opt] / t[bf]):>14.1f}%"
              f"{100 * t['voraz ya óptimo']:>16.0f}%")
    print("\nAhorro B-F: Bellman-Ford frente a BFS, con el mismo orden voraz (esquivar la congestión).")
    print("Ahorro óptimo: orden de Held-Karp frente al voraz, los dos con Bellman-Ford (ordenar mejor).")
    print(f"Tiempo de cálculo medio con 8 productos: {tabla[-1][bfs + ' ms']:.0f} ms (BFS), "
          f"{tabla[-1][bf + ' ms']:.0f} ms (B-F voraz), {tabla[-1][opt + ' ms']:.0f} ms (B-F óptimo).")

    fig, ax = plt.subplots(figsize=(8.5, 5))
    ancho = 0.27
    for j, (nombre, _, _, color) in enumerate(ESTRATEGIAS):
        xs = [i + (j - 1) * ancho for i in range(len(tabla))]
        barras = ax.bar(xs, [t[nombre] for t in tabla], ancho, color=color, label=nombre)
        ax.bar_label(barras, fmt="%.0f", fontsize=8)
    ax.set_xticks(range(len(tabla)), [f"{t['Productos']} productos" for t in tabla])
    ax.set_ylabel("Tiempo medio de caminata (s)")
    ax.set_title(f"KivaFlow: {args.pedidos} pedidos por tamaño, salen de un muelle de Despacho y terminan en el más cercano", fontsize=10)
    ax.grid(axis="y", alpha=0.3)
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(SALIDA / "experimento_pedidos.png", dpi=110)
    print("\nArchivos: resultados/experimento_pedidos.csv y resultados/experimento_pedidos.png")
    if not args.sin_ventana:
        print("Abriendo la gráfica (ciérrala para terminar)…")
        plt.show()


if __name__ == "__main__":
    main()
