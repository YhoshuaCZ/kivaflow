"""Compara BFS y Bellman-Ford en pedidos de distinto tamaño y hora, y calcula los cuellos de botella.

Uso: python scripts/experimentos.py   -> resultados/experimentos.csv, resultados/resumen.md y figuras
"""
import csv
import random
import statistics
import sys
import time
from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.collections import LineCollection  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from kivaflow import config, edmonds_karp as ek, grafo, pedido  # noqa: E402

TAMANOS = (1, 5, 10)
PERFILES = ("valle", "punta")
PEDIDOS_POR_ESCENARIO = 30
SALIDA = RAIZ / "resultados"


def generar_pedidos(nodos, rng):
    """Pedidos con la popularidad de skus.csv (sintética o Instacart, la que se haya generado)."""
    with open(RAIZ / "data" / "skus.csv", newline="", encoding="utf-8") as f:
        pop = {r["SKU"]: int(r["Veces_Pedido"]) for r in csv.DictReader(f)}
    rack_de = {d["SKU"]: n for n, d in nodos.items() if d["SKU"]}
    skus = sorted(rack_de)
    pesos = [pop.get(s, 0) + 1 for s in skus]
    muelles = sorted(n for n, d in nodos.items() if d["Tipo"] == "estacion" and int(d["Columna"]) == config.COLUMNAS - 1)
    pedidos = {}
    for k in TAMANOS:
        lista = []
        for _ in range(PEDIDOS_POR_ESCENARIO):
            elegidos = set()
            while len(elegidos) < k:
                elegidos.add(rng.choices(skus, weights=pesos)[0])
            lista.append((rng.choice(muelles), [rack_de[s] for s in sorted(elegidos)]))
        pedidos[k] = lista
    return pedidos


def correr_rutas(nodos, aristas):
    por_par = {frozenset((a["Nodo_Origen"], a["Nodo_Destino"])): a for a in aristas}
    pedidos = generar_pedidos(nodos, random.Random(config.SEMILLA))
    filas = []
    for perfil in PERFILES:
        ady = grafo.adyacencia(aristas, perfil)
        dirigidas = grafo.lista_de_aristas(ady)
        for k in TAMANOS:
            for i, (muelle, racks) in enumerate(pedidos[k]):
                for estrategia in ("bfs", "bellman_ford"):
                    r = pedido.ruta_pedido(ady, dirigidas, muelle, racks, estrategia)
                    m = pedido.medir(r["camino"], por_par, perfil)
                    filas.append({"perfil": perfil, "productos": k, "pedido": i, "estrategia": estrategia, **m,
                                  "nodos_visitados": r["nodos_visitados"], "relajaciones": r["relajaciones"],
                                  "ms": round(r["segundos"] * 1000, 2)})
            print(f"  {perfil}, {k} productos: listo")
    return filas


def resumir(filas):
    grupos = {}
    for f in filas:
        grupos.setdefault((f["perfil"], f["productos"], f["estrategia"]), []).append(f)
    tabla = []
    for perfil in PERFILES:
        for k in TAMANOS:
            b, bf = grupos[(perfil, k, "bfs")], grupos[(perfil, k, "bellman_ford")]
            media = lambda xs, c: statistics.mean(x[c] for x in xs)  # noqa: E731
            tabla.append({
                "perfil": perfil, "productos": k,
                "bfs_pasillos": media(b, "pasillos"), "bf_pasillos": media(bf, "pasillos"),
                "bfs_tiempo_s": media(b, "tiempo_s"), "bf_tiempo_s": media(bf, "tiempo_s"),
                "ahorro_pct": 100 * (1 - media(bf, "tiempo_s") / media(b, "tiempo_s")),
                "bfs_visitados": media(b, "nodos_visitados"), "bf_relajaciones": media(bf, "relajaciones"),
                "bfs_ms": media(b, "ms"), "bf_ms": media(bf, "ms"),
            })
    return tabla


def figura_ruta(nodos, aristas, salida):
    """Un pedido de 5 productos en hora punta: ruta BFS vs. ruta Bellman-Ford."""
    pos = {k: (float(n["X_m"]), -float(n["Y_m"])) for k, n in nodos.items()}
    ady = grafo.adyacencia(aristas, "punta")
    muelle, racks = generar_pedidos(nodos, random.Random(config.SEMILLA))[5][0]
    rutas = {e: pedido.ruta_pedido(ady, grafo.lista_de_aristas(ady), muelle, racks, e)["camino"]
             for e in ("bfs", "bellman_ford")}
    por_par = {frozenset((a["Nodo_Origen"], a["Nodo_Destino"])): a for a in aristas}

    fig, ax = plt.subplots(figsize=(10, 11))
    colores = {"Baja": "#e2e8f0", "Media": "#fbd38d", "Alta": "#feb2b2"}
    for nivel, c in colores.items():
        seg = [(pos[a["Nodo_Origen"]], pos[a["Nodo_Destino"]]) for a in aristas if a["Frecuencia_Pedidos"] == nivel]
        ax.add_collection(LineCollection(seg, colors=c, linewidths=1.2, label=f"Congestión {nivel.lower()}"))
    for e, (color, ancho) in {"bfs": ("#2b6cb0", 4), "bellman_ford": ("#2f855a", 2)}.items():
        m = pedido.medir(rutas[e], por_par, "punta")
        xs, ys = zip(*(pos[n] for n in rutas[e]))
        nombre = "BFS" if e == "bfs" else "Bellman-Ford"
        ax.plot(xs, ys, color=color, lw=ancho, alpha=0.85,
                label=f"{nombre}: {m['pasillos']} pasillos, {m['tiempo_s']} s")
    ax.scatter(*zip(*(pos[r] for r in racks)), s=120, c="#c53030", zorder=5, label="Racks del pedido")
    ax.scatter(*pos[muelle], s=180, c="black", marker="s", zorder=5, label="Muelle de despacho")
    ax.set_title("Pedido de 5 productos en hora punta")
    ax.set_aspect("equal")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.04), ncol=2, fontsize=9)
    fig.savefig(salida, dpi=100, bbox_inches="tight")
    plt.close(fig)


def flujo(nodos, aristas, salida_png):
    cap = grafo.capacidades(aristas)
    t0 = time.perf_counter()
    valor, _, cuellos, stats = ek.entre_zonas(cap, nodos, "Recepción y Almacenamiento", "Empaque y Despacho")
    ms = (time.perf_counter() - t0) * 1000

    pos = {k: (float(n["X_m"]), -float(n["Y_m"])) for k, n in nodos.items()}
    fig, ax = plt.subplots(figsize=(10, 11))
    ax.add_collection(LineCollection([(pos[a["Nodo_Origen"]], pos[a["Nodo_Destino"]]) for a in aristas],
                                     colors="#e2e8f0", linewidths=1))
    ax.add_collection(LineCollection([(pos[u], pos[v]) for u, v, _ in cuellos], colors="#c53030", linewidths=3,
                                     label=f"Corte mínimo: {len(cuellos)} pasillos saturados"))
    ax.scatter(*zip(*(pos[n] for n in stats["lado_fuente"] if n in pos)), s=3, c="#2b6cb0",
               label="Lado de Recepción del corte")
    ax.set_title(f"Flujo máximo Recepción → Despacho: {valor} operarios/min")
    ax.set_aspect("equal")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.04), ncol=2, fontsize=9)
    fig.savefig(salida_png, dpi=100, bbox_inches="tight")
    plt.close(fig)

    columnas = Counter(int(nodos[u]["Columna"]) for u, _, _ in cuellos)
    niveles = Counter(next(a["Frecuencia_Pedidos"] for a in aristas
                           if {a["Nodo_Origen"], a["Nodo_Destino"]} == {u, v}) for u, v, _ in cuellos)
    return {"valor": valor, "pasillos_corte": len(cuellos), "caminos_aumento": stats["caminos_aumento"],
            "ms": round(ms, 1), "columnas": columnas, "niveles": niveles}


def main():
    SALIDA.mkdir(exist_ok=True)
    nodos, aristas = grafo.leer_nodos(), grafo.leer_aristas()
    print("Rutas de picking (BFS vs. Bellman-Ford)...")
    filas = correr_rutas(nodos, aristas)
    with open(SALIDA / "experimentos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    tabla = resumir(filas)
    print("Flujo máximo (Edmonds-Karp)...")
    fl = flujo(nodos, aristas, SALIDA / "cuellos_de_botella.png")
    figura_ruta(nodos, aristas, SALIDA / "ruta_ejemplo.png")

    with open(RAIZ / "data" / "skus.csv", encoding="utf-8") as f:
        fuente = f.readlines()[1].strip().split(",")[-1]
    lineas = [
        "# Resultados de los experimentos",
        "",
        f"> Generado por `scripts/experimentos.py`. Demanda: **{fuente}**. "
        f"{PEDIDOS_POR_ESCENARIO} pedidos por escenario; cada uno sale de un muelle de despacho, "
        "visita sus racks en orden de vecino más cercano y vuelve. Los tiempos en ms dependen de la PC. "
        "*Nodos visitados* y *relajaciones* suman todas las búsquedas del pedido (k productos = k + 1 búsquedas). "
        "*Tiempo* es el tiempo estimado de caminata del operario (distancia ajustada / 1,1 m/s).",
        "",
        "## Rutas de picking: BFS vs. Bellman-Ford (promedios por pedido)",
        "",
        "| Hora | Productos | Pasillos BFS | Pasillos B-F | Tiempo BFS (s) | Tiempo B-F (s) | Ahorro B-F | Nodos visitados BFS | Relajaciones B-F | ms BFS | ms B-F |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for t in tabla:
        lineas.append(f"| {t['perfil']} | {t['productos']} | {t['bfs_pasillos']:.1f} | {t['bf_pasillos']:.1f} | "
                      f"{t['bfs_tiempo_s']:.1f} | {t['bf_tiempo_s']:.1f} | {t['ahorro_pct']:.1f} % | "
                      f"{t['bfs_visitados']:.0f} | {t['bf_relajaciones']:.0f} | {t['bfs_ms']:.1f} | {t['bf_ms']:.1f} |")
    lineas += [
        "",
        "![Ruta de ejemplo](ruta_ejemplo.png)",
        "",
        "## Cuellos de botella: Edmonds-Karp (Recepción → Despacho)",
        "",
        "| Flujo máximo | Pasillos en el corte mínimo | Caminos de aumento | ms |",
        "|---|---|---|---|",
        f"| {fl['valor']} operarios/min | {fl['pasillos_corte']} | {fl['caminos_aumento']} | {fl['ms']} |",
        "",
        f"Congestión de los pasillos del corte: {dict(fl['niveles'])}. "
        f"Columnas donde está el corte: {dict(sorted(fl['columnas'].items()))}.",
        "",
        "![Cuellos de botella](cuellos_de_botella.png)",
        "",
    ]
    (SALIDA / "resumen.md").write_text("\n".join(lineas), encoding="utf-8")
    print(f"Escrito {SALIDA / 'resumen.md'}")


if __name__ == "__main__":
    main()
