"""Bellman-Ford: la ruta de MENOR COSTO considerando la congestión de cada pasillo.

Idea: en un grafo de V nodos un camino mínimo tiene a lo sumo V - 1 aristas. Si en
cada "ronda" se intenta mejorar (relajar) todas las aristas, tras la ronda k ya están
bien calculados todos los caminos mínimos de hasta k aristas. Con V - 1 rondas basta.
Si en la ronda V todavía se puede mejorar algo, hay un ciclo de peso negativo.

Optimización: si una ronda entera no mejora nada, ya terminó (salida anticipada).
En la cuadrícula del almacén eso pasa tras unas ~100 rondas en vez de 1799.

Complejidad: O(V · E) tiempo en el peor caso, O(V) memoria (dist + padre).
"""
from math import inf

from .bfs import reconstruir


class CicloNegativo(Exception):
    pass


def bellman_ford(nodos, aristas, origen):
    """aristas: [(u, v, w), ...] dirigidas.

    Devuelve (dist, padre, stats) con stats = {"rondas", "relajaciones"}.
    Lanza CicloNegativo si alguno es alcanzable desde el origen.
    """
    dist = {n: inf for n in nodos}
    padre = {n: None for n in nodos}
    dist[origen] = 0.0
    rondas = relajaciones = 0
    for _ in range(len(dist) - 1):
        rondas += 1
        cambio = False
        for u, v, w in aristas:
            du = dist[u]
            if du + w < dist[v]:
                dist[v] = du + w
                padre[v] = u
                relajaciones += 1
                cambio = True
        if not cambio:
            break
    else:
        # Se hicieron las V - 1 rondas: una más para detectar ciclos negativos.
        for u, v, w in aristas:
            if dist[u] + w < dist[v]:
                raise CicloNegativo(f"ciclo negativo alcanzable desde {origen} (arista {u}->{v})")
    return dist, padre, {"rondas": rondas, "relajaciones": relajaciones}


def ruta(nodos, aristas, origen, destino):
    """Devuelve (camino, costo, stats)."""
    dist, padre, stats = bellman_ford(nodos, aristas, origen)
    if dist[destino] == inf:
        return [], inf, stats
    return reconstruir(padre, destino), dist[destino], stats
