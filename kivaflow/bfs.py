"""Búsqueda en anchura (BFS): la ruta con MENOS pasillos, ignorando la congestión.

Es la línea base del trabajo. Explora por niveles con una cola FIFO: primero todos
los nodos a 1 pasillo del origen, luego a 2, etc. Por eso, la primera vez que llega
al destino lo hace con el mínimo número de aristas.

Complejidad: O(V + E) tiempo (cada nodo entra una vez a la cola y cada arista se
mira una vez por extremo) y O(V) memoria (cola + padres).
"""
from collections import deque


def bfs(ady, origen, destino):
    """Devuelve (camino, nodos_visitados). camino = [] si no hay ruta.

    `destino` puede ser un nodo o un conjunto de nodos: en ese caso se detiene en el
    primero que saca de la cola, que es el más cercano en número de pasillos.
    """
    destinos = destino if isinstance(destino, (set, frozenset)) else {destino}
    padre = {origen: None}
    cola = deque([origen])
    visitados = 0
    while cola:
        u = cola.popleft()
        visitados += 1
        if u in destinos:
            return reconstruir(padre, u), visitados
        for v, _ in ady.get(u, ()):
            if v not in padre:
                padre[v] = u
                cola.append(v)
    return [], visitados


def bfs_distancias(ady, origen):
    """Número de pasillos desde `origen` hasta cada nodo alcanzable (sin salida anticipada)."""
    dist = {origen: 0}
    cola = deque([origen])
    while cola:
        u = cola.popleft()
        for v, _ in ady.get(u, ()):
            if v not in dist:
                dist[v] = dist[u] + 1
                cola.append(v)
    return dist


def reconstruir(padre, destino):
    camino = []
    while destino is not None:
        camino.append(destino)
        destino = padre[destino]
    return camino[::-1]
