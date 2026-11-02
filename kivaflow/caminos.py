"""Caminos mínimos, a mano: BFS (línea base, cuenta pasillos) y la programación
dinámica en grafos de la hoja 13 (Bellman-Ford y Floyd-Warshall)."""
from collections import deque
from dataclasses import dataclass

INF = float("inf")


@dataclass
class BellmanFord:
    dist: dict
    padre: dict
    rondas: int  # rondas de relajación hasta que nada cambió
    relajaciones: int  # veces que se mejoró una distancia
    ciclo_negativo: bool


def bellman_ford(nodos, arcos, origen, al_evento=None):
    """arcos: [(u, v, w)] dirigidos. Hasta V - 1 rondas; para antes si una ronda no
    mejora nada. Una ronda extra que todavía mejora indica un ciclo negativo.

    `al_evento(v)`, si se da, se llama cada vez que mejora la distancia de v
    (lo usa la animación en el tiempo)."""
    dist = {n: INF for n in nodos}
    padre = {n: None for n in nodos}
    dist[origen] = 0.0
    rondas = relajaciones = 0
    for _ in range(len(dist) - 1):
        rondas += 1
        cambio = False
        for u, v, w in arcos:
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                padre[v] = u
                relajaciones += 1
                cambio = True
                if al_evento:
                    al_evento(v)
        if not cambio:
            break
    negativo = any(dist[u] + w < dist[v] for u, v, w in arcos)
    return BellmanFord(dist, padre, rondas, relajaciones, negativo)


def bfs(nodos, arcos, origen, al_evento=None):
    """Menor número de pasillos desde `origen` (todos los pasos valen 1). O(V + E).

    Devuelve (dist, padre). Es la línea base: no ve la congestión.
    `al_evento(v)`, si se da, se llama cuando BFS descubre v.
    """
    ady = {n: [] for n in nodos}
    for u, v, *_ in arcos:
        ady[u].append(v)
    dist, padre = {origen: 0}, {n: None for n in nodos}
    cola = deque([origen])
    while cola:
        u = cola.popleft()
        for v in ady[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                padre[v] = u
                cola.append(v)
                if al_evento:
                    al_evento(v)
    return dist, padre


def camino(padre, destino):
    c = [destino]
    while padre[c[-1]] is not None:
        c.append(padre[c[-1]])
    return c[::-1]


def floyd_warshall(nodos, arcos):
    """Todos contra todos en O(V³). dist[i][j] y sig[i][j] (siguiente nodo del camino).

    Recurrencia de DP: con los nodos 0..k como intermedios,
    d_k(i, j) = min(d_{k-1}(i, j), d_{k-1}(i, k) + d_{k-1}(k, j)).
    """
    nodos = list(nodos)
    idx = {n: i for i, n in enumerate(nodos)}
    n = len(nodos)
    dist = [[INF] * n for _ in range(n)]
    sig = [[None] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0.0
        sig[i][i] = i
    for u, v, w in arcos:
        i, j = idx[u], idx[v]
        if w < dist[i][j]:
            dist[i][j] = w
            sig[i][j] = j
    for k in range(n):
        dk = dist[k]
        for i in range(n):
            dik = dist[i][k]
            if dik == INF:
                continue
            di, si = dist[i], sig[i]
            for j in range(n):
                if dik + dk[j] < di[j]:
                    di[j] = dik + dk[j]
                    si[j] = si[k]
    return nodos, dist, sig


def camino_fw(nodos, sig, origen, destino):
    idx = {n: i for i, n in enumerate(nodos)}
    i, j = idx[origen], idx[destino]
    if sig[i][j] is None:
        return []
    c = [i]
    while i != j:
        i = sig[i][j]
        c.append(i)
    return [nodos[x] for x in c]
