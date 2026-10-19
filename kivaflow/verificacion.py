"""Verificación: nuestros algoritmos contra NetworkX (la referencia) en muchas consultas.

NetworkX es una librería de grafos usada en la industria y la investigación
(Hagberg et al., 2008). Si en cientos de consultas al azar nuestras implementaciones
dan exactamente lo mismo, la implementación es correcta para este grafo.
Es la sección «Validación de resultados y pruebas» del informe.
"""
import datetime
import platform
import random
import sys
import time

import networkx as nx

from . import bellman_ford as bf
from . import config, edmonds_karp as ek, grafo
from .bfs import bfs

ZONAS = [z for z, _ in config.ZONAS]


def _nx(aristas, perfil):
    g = nx.Graph()
    for a in aristas:
        g.add_edge(a["Nodo_Origen"], a["Nodo_Destino"], weight=grafo.peso(a, perfil))
    return g


def verificar(nodos, aristas, consultas_bfs=300, consultas_bf=150, semilla=2026, progreso=None):
    """Devuelve un dict con aciertos y error máximo por algoritmo, y los datos del entorno."""
    rng = random.Random(semilla)
    ids = sorted(nodos)
    res = {}
    t0 = time.perf_counter()

    # BFS: misma cantidad de pasillos que nx.shortest_path_length y ruta legal
    ady = grafo.adyacencia(aristas, "punta")
    g = _nx(aristas, "punta")
    ok = 0
    for i in range(consultas_bfs):
        s, t = rng.sample(ids, 2)
        camino, _ = bfs(ady, s, t)
        legal = camino[0] == s and camino[-1] == t and all(g.has_edge(u, v) for u, v in zip(camino, camino[1:]))
        ok += legal and len(camino) - 1 == nx.shortest_path_length(g, s, t)
        if progreso:
            progreso((i + 1) / (consultas_bfs + 2 * consultas_bf + 6))
    res["bfs"] = {"consultas": consultas_bfs, "aciertos": ok, "error_max": 0.0,
                  "criterio": "misma longitud (pasillos) que networkx.shortest_path_length y ruta legal"}

    # Bellman-Ford: misma distancia que nx.bellman_ford_path_length, en punta y en valle
    ok, err, hechas = 0, 0.0, 0
    for perfil in ("punta", "valle"):
        ady = grafo.adyacencia(aristas, perfil)
        dirigidas = grafo.lista_de_aristas(ady)
        g = _nx(aristas, perfil)
        for _ in range(consultas_bf):
            s, t = rng.sample(ids, 2)
            camino, costo, _ = bf.ruta(ady.keys(), dirigidas, s, t)
            ref = nx.bellman_ford_path_length(g, s, t)
            e = abs(costo - ref)
            err = max(err, e)
            ok += e < 1e-9 and camino[0] == s and camino[-1] == t
            hechas += 1
            if progreso:
                progreso((consultas_bfs + hechas) / (consultas_bfs + 2 * consultas_bf + 6))
    res["bellman_ford"] = {"consultas": hechas, "aciertos": ok, "error_max": err,
                           "criterio": "misma distancia que networkx.bellman_ford_path_length (punta y valle)"}

    # Edmonds-Karp: mismo flujo máximo que nx.maximum_flow_value entre cada par de zonas
    cap = grafo.capacidades(aristas)
    ok, hechas = 0, 0
    for a in ZONAS:
        for b in ZONAS:
            if a == b:
                continue
            valor, _, cuellos, _ = ek.entre_zonas(cap, nodos, a, b)
            d = nx.DiGraph()
            for u, vec in cap.items():
                for v, c in vec.items():
                    d.add_edge(u, v, capacity=c)
            for n, datos in nodos.items():
                if datos["Zona"] == a:
                    d.add_edge("S", n)
                if datos["Zona"] == b:
                    d.add_edge(n, "T")
            ok += valor == nx.maximum_flow_value(d, "S", "T") and sum(c for _, _, c in cuellos) == valor
            hechas += 1
            if progreso:
                progreso((consultas_bfs + 2 * consultas_bf + hechas) / (consultas_bfs + 2 * consultas_bf + 6))
    res["edmonds_karp"] = {"consultas": hechas, "aciertos": ok, "error_max": 0.0,
                           "criterio": "mismo valor que networkx.maximum_flow_value y corte = flujo, "
                                       "entre cada par ordenado de zonas"}

    return {
        "algoritmos": res,
        "segundos": round(time.perf_counter() - t0, 1),
        "fecha": datetime.date.today().isoformat(),
        "python": platform.python_version(),
        "networkx": nx.__version__,
        "sistema": "navegador (Pyodide)" if sys.platform == "emscripten" else platform.platform(),
        "semilla": semilla,
    }
