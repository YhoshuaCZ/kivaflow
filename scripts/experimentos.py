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

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from kivaflow import config, edmonds_karp as ek, grafo, paleta, pedido, visual  # noqa: E402

TAMANOS = (1, 5, 10)
PERFILES = ("valle", "punta")
PEDIDOS_POR_ESCENARIO = 30
SALIDA = RAIZ / "resultados"


def generar_pedidos(nodos, popularidad):
    rng = random.Random(config.SEMILLA)
    return {k: [pedido.aleatorio(nodos, popularidad, k, rng) for _ in range(PEDIDOS_POR_ESCENARIO)] for k in TAMANOS}


def correr_rutas(nodos, aristas, pedidos):
    por_par = {frozenset((a["Nodo_Origen"], a["Nodo_Destino"])): a for a in aristas}
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

    def media(xs, c):
        return statistics.mean(x[c] for x in xs)

    tabla = []
    for perfil in PERFILES:
        for k in TAMANOS:
            b, bf = grupos[(perfil, k, "bfs")], grupos[(perfil, k, "bellman_ford")]
            tabla.append({
                "perfil": perfil, "productos": k,
                "bfs_pasillos": media(b, "pasillos"), "bf_pasillos": media(bf, "pasillos"),
                "bfs_tiempo_s": media(b, "tiempo_s"), "bf_tiempo_s": media(bf, "tiempo_s"),
                "ahorro_pct": 100 * (1 - media(bf, "tiempo_s") / media(b, "tiempo_s")),
                "bfs_visitados": media(b, "nodos_visitados"), "bf_relajaciones": media(bf, "relajaciones"),
                "bfs_ms": media(b, "ms"), "bf_ms": media(bf, "ms"),
            })
    return tabla


def figura_ruta(nodos, aristas, muelle, racks, salida):
    """Un pedido de 5 productos en hora punta: ruta BFS vs. ruta Bellman-Ford."""
    ady = grafo.adyacencia(aristas, "punta")
    dirigidas = grafo.lista_de_aristas(ady)
    por_par = {frozenset((a["Nodo_Origen"], a["Nodo_Destino"])): a for a in aristas}
    caminos = {}
    for e, nombre, color, ancho in (("bfs", "BFS", paleta.ALGORITMO["bfs"], 4),
                                   ("bellman_ford", "Bellman-Ford", paleta.ALGORITMO["bellman_ford"], 2)):
        camino = pedido.ruta_pedido(ady, dirigidas, muelle, racks, e)["camino"]
        m = pedido.medir(camino, por_par, "punta")
        caminos[f"{nombre}: {m['pasillos']} pasillos, {m['tiempo_s']} s"] = (camino, color, ancho)
    fig = visual.rutas(nodos, aristas, caminos, racks, muelle, "Pedido de 5 productos en hora punta")
    fig.savefig(salida, dpi=100, bbox_inches="tight")


def flujo(nodos, aristas, salida_png):
    cap = grafo.capacidades(aristas)
    t0 = time.perf_counter()
    valor, _, cuellos, stats = ek.entre_zonas(cap, nodos, "Recepción y Almacenamiento", "Empaque y Despacho")
    ms = (time.perf_counter() - t0) * 1000
    fig = visual.corte(nodos, aristas, cuellos, stats["lado_fuente"],
                       f"Flujo máximo Recepción → Despacho: {valor} operarios/min")
    fig.savefig(salida_png, dpi=100, bbox_inches="tight")

    por_par = {frozenset((a["Nodo_Origen"], a["Nodo_Destino"])): a for a in aristas}
    return {"valor": valor, "pasillos_corte": len(cuellos), "caminos_aumento": stats["caminos_aumento"],
            "ms": round(ms, 1),
            "columnas": Counter(int(nodos[u]["Columna"]) for u, _, _ in cuellos),
            "niveles": Counter(por_par[frozenset((u, v))]["Frecuencia_Pedidos"] for u, v, _ in cuellos)}


def main():
    SALIDA.mkdir(exist_ok=True)
    nodos, aristas = grafo.leer_nodos(), grafo.leer_aristas()
    popularidad, fuente = grafo.leer_popularidad()
    pedidos = generar_pedidos(nodos, popularidad)

    print("Rutas de picking (BFS vs. Bellman-Ford)...")
    filas = correr_rutas(nodos, aristas, pedidos)
    with open(SALIDA / "experimentos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    tabla = resumir(filas)
    print("Flujo máximo (Edmonds-Karp)...")
    fl = flujo(nodos, aristas, SALIDA / "cuellos_de_botella.png")
    figura_ruta(nodos, aristas, *pedidos[5][0], SALIDA / "ruta_ejemplo.png")

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
    (SALIDA / "resumen.md").write_text("\n".join(lineas), encoding="utf-8", newline="\n")
    print(f"Escrito {SALIDA / 'resumen.md'}")


if __name__ == "__main__":
    main()
