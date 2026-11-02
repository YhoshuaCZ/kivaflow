"""Análisis de eficiencia: cómo crecen el tiempo, la memoria y las operaciones de cada
algoritmo cuando el almacén crece.

Se toman sectores cuadrados del almacén (10 × 10, 15 × 15, … hasta el almacén
completo de 45 × 40) y en cada uno se corre cada algoritmo. Con los puntos
(V, tiempo) se ajusta una recta en escala log-log: su pendiente k dice que el
tiempo crece como V^k, y se compara con la complejidad teórica.

En esta cuadrícula E ≈ 2V, así que O(V + E) = O(V), O(E log V) ≈ O(V log V),
O(V · E) ≈ O(V²) y O(V³) se queda en O(V³).

Uso:
    python scripts/analisis.py            # tabla en consola + resultados/escalabilidad.{csv,png}
    python scripts/analisis.py --rapido   # menos tamaños (para probar)
"""
import argparse
import csv
import math
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from kivaflow import config  # noqa: E402
from kivaflow.caminos import bellman_ford, bfs, floyd_warshall  # noqa: E402
from kivaflow.flujo import edmonds_karp, red  # noqa: E402
from kivaflow.medicion import medir  # noqa: E402
from kivaflow.mst import kruskal, prim  # noqa: E402

SALIDA = RAIZ / "resultados"
TEORICA = {  # complejidad y exponente esperado en V cuando E ≈ 2V
    "BFS": ("O(V + E)", 1.0),
    "Bellman-Ford": ("O(V · E)", 2.0),
    "Kruskal + UFDS": ("O(E log E)", 1.1),
    "Prim (heap)": ("O(E log V)", 1.1),
    "Edmonds-Karp": ("O(V · E²)", 3.0),
    "Floyd-Warshall": ("O(V³)", 3.0),
}
COLOR = {"BFS": "#718096", "Bellman-Ford": "#2b6cb0", "Kruskal + UFDS": "#2f855a", "Prim (heap)": "#68d391",
         "Edmonds-Karp": "#e53e3e", "Floyd-Warshall": "#805ad5"}
FW_MAX_V = 225  # Floyd-Warshall en Python puro: con 400 nodos ya son 6,4 × 10⁷ pasos


def sector(d, filas, cols):
    nodos = d.sector(range(filas), range(cols))
    dentro = set(nodos)
    return nodos, dentro, [a for a in d.filas if a["Nodo_Origen"] in dentro and a["Nodo_Destino"] in dentro]


def correr(d, filas, cols):
    nodos, dentro, filas_csv = sector(d, filas, cols)
    aristas = d.aristas(dentro=dentro)
    arcos = aristas + [(v, u, w) for u, v, w in aristas]
    origen = nodos[0]
    izq = [n for n in nodos if int(d.nodos[n]["Columna"]) == 0]
    der = [n for n in nodos if int(d.nodos[n]["Columna"]) == cols - 1]
    cap = red(filas_csv, config.CAPACIDAD_OPERARIOS_MIN, izq, der)

    casos = {
        "BFS": (lambda: bfs(nodos, arcos, origen), lambda r: f"{len(r[0])} nodos visitados"),
        "Bellman-Ford": (lambda: bellman_ford(nodos, arcos, origen),
                         lambda r: f"{r.rondas} rondas, {r.rondas * len(arcos)} arcos revisados"),
        "Kruskal + UFDS": (lambda: kruskal(nodos, aristas), lambda r: f"{r.revisadas} aristas revisadas"),
        "Prim (heap)": (lambda: prim(nodos, aristas), lambda r: f"{r.revisadas} entradas del heap"),
        "Edmonds-Karp": (lambda: edmonds_karp(cap), lambda r: f"{len(r.caminos)} caminos, flujo {r.valor}"),
    }
    if len(nodos) <= FW_MAX_V:
        casos["Floyd-Warshall"] = (lambda: floyd_warshall(nodos, arcos), lambda r: f"{len(nodos) ** 3} pasos (V³)")
    filas_salida = []
    for nombre, (f, ops) in casos.items():
        r, ms, kb = medir(f, repeticiones=1 if nombre == "Floyd-Warshall" else 3)
        filas_salida.append({"Algoritmo": nombre, "Sector": f"{filas}x{cols}", "V": len(nodos), "E": len(aristas),
                             "Tiempo_ms": round(ms, 3), "Memoria_pico_KB": round(kb, 1), "Operaciones": ops(r)})
    return filas_salida


def pendiente(xs, ys):
    """Mínimos cuadrados de log(y) contra log(x): el exponente k de y ≈ c · x^k."""
    lx, ly = [math.log(x) for x in xs], [math.log(max(y, 1e-6)) for y in ys]
    mx, my = sum(lx) / len(lx), sum(ly) / len(ly)
    return sum((a - mx) * (b - my) for a, b in zip(lx, ly)) / sum((a - mx) ** 2 for a in lx)


def main():
    from demo import Datos
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--rapido", action="store_true")
    args = p.parse_args()
    tamanos = [(10, 10), (15, 15), (25, 25), (45, 40)] if args.rapido else \
        [(10, 10), (12, 12), (15, 15), (20, 20), (25, 25), (30, 30), (35, 35), (40, 40), (45, 40)]
    d = Datos()
    filas = []
    for f, c in tamanos:
        print(f"Sector {f} x {c} ({f * c} ubicaciones)…", flush=True)
        filas += correr(d, f, c)

    SALIDA.mkdir(exist_ok=True)
    with open(SALIDA / "escalabilidad.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)

    print(f"\n{'Algoritmo':<16}{'Teórica':<13}{'Esperado':>9}{'Medido':>8}   Tiempo y memoria en el almacén completo")
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(13, 5.2))
    for nombre, (comp, esperado) in TEORICA.items():
        pts = [r for r in filas if r["Algoritmo"] == nombre]
        xs, ts, ms = [r["V"] for r in pts], [r["Tiempo_ms"] for r in pts], [r["Memoria_pico_KB"] for r in pts]
        k = pendiente(xs, ts)
        ultimo = pts[-1]
        print(f"{nombre:<16}{comp:<13}{'V^' + format(esperado, '.1f'):>9}{'V^' + format(k, '.2f'):>8}   "
              f"{ultimo['Tiempo_ms']:.1f} ms y {ultimo['Memoria_pico_KB']:.0f} KB con V = {ultimo['V']}")
        a1.plot(xs, ts, "o-", color=COLOR[nombre], label=f"{nombre}: medido V^{k:.2f} ({comp})")
        a2.plot(xs, ms, "o-", color=COLOR[nombre], label=nombre)
    for ax, t in ((a1, "Tiempo (ms), escala log-log"), (a2, "Memoria pico (KB), escala log-log")):
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel("V (ubicaciones del sector)")
        ax.set_title(t, fontsize=10)
        ax.grid(True, which="both", alpha=0.3)
    a1.legend(fontsize=7.5)
    a2.legend(fontsize=7.5)
    fig.suptitle("KivaFlow: cómo crecen tiempo y memoria con el tamaño del almacén", fontsize=11)
    fig.tight_layout()
    fig.savefig(SALIDA / "escalabilidad.png", dpi=110)
    print("\nPor qué el medido puede diferir del teórico:")
    print("- Bellman-Ford para apenas una ronda no mejora nada. Desde una esquina, y con los arcos en el orden del CSV")
    print("  (fila por fila), las distancias se propagan casi en una sola pasada: 2 a 5 rondas en vez de V - 1.")
    print("  Así cuesta ≈ rondas · E, casi lineal. Desde otros orígenes hacen falta más rondas (ver la app).")
    print("- Edmonds-Karp: O(V · E²) es una cota de peor caso. Aquí hace ≈ √V caminos de aumento (el flujo es chico)")
    print("  y cada BFS cuesta O(V + E): √V · V = V^1.5, que es lo que se mide.")
    print("- Kruskal y Prim: el log V casi no se nota con tamaños tan pequeños; se ven casi lineales.")
    print("\nArchivos: resultados/escalabilidad.csv y resultados/escalabilidad.png")


if __name__ == "__main__":
    main()
