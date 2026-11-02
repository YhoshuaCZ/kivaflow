"""Ruta de *picking* de un pedido: salir de un punto, recoger varios productos y
(opcionalmente) terminar en un muelle de Despacho.

Un pedido real casi nunca es de un solo producto, por eso hay varios destinos.
Elegir el mejor orden para visitarlos es un problema del viajante (NP-difícil), así
que se usa una regla **voraz**: desde donde está, el operario va al producto
pendiente más cercano. Cada tramo es un camino mínimo calculado con BFS (menos
pasillos) o con Bellman-Ford (menor distancia ajustada por congestión).
"""
from collections import defaultdict

from kivaflow.caminos import bellman_ford, bfs, camino


class Buscador:
    """Precalcula la lista de adyacencia una vez y cuenta las operaciones de cada búsqueda."""

    def __init__(self, nodos, arcos, algoritmo):
        self.nodos, self.arcos, self.algoritmo = list(nodos), arcos, algoritmo
        self.grado = defaultdict(int)
        for u, *_ in arcos:
            self.grado[u] += 1
        self.ops = defaultdict(int)

    def desde(self, origen):
        """(dist, padre) desde `origen` y suma sus operaciones a `self.ops`."""
        self.ops["búsquedas (una por tramo)"] += 1
        if self.algoritmo == "BFS":
            dist, padre = bfs(self.nodos, self.arcos, origen)
            self.ops["nodos visitados"] += len(dist)
            self.ops["arcos revisados"] += sum(self.grado[n] for n in dist)
            return dist, padre
        b = bellman_ford(self.nodos, self.arcos, origen)
        self.ops["rondas de relajación"] += b.rondas
        self.ops["arcos revisados"] += b.rondas * len(self.arcos) + len(self.arcos)  # + ronda de ciclo negativo
        self.ops["relajaciones"] += b.relajaciones
        return b.dist, b.padre


def ruta_pedido(buscador, origen, productos, muelles_finales=()):
    """Devuelve (recorrido completo, orden de visita).

    `muelles_finales`: si hay, el recorrido termina en el más cercano al último producto.
    """
    pendientes, actual = list(dict.fromkeys(productos)), origen
    recorrido, orden = [origen], []
    while pendientes:
        dist, padre = buscador.desde(actual)
        siguiente = min(pendientes, key=lambda p: (dist.get(p, float("inf")), p))
        recorrido += camino(padre, siguiente)[1:]
        orden.append(siguiente)
        pendientes.remove(siguiente)
        actual = siguiente
    if muelles_finales:
        dist, padre = buscador.desde(actual)
        muelle = min(muelles_finales, key=lambda m: (dist.get(m, float("inf")), m))
        recorrido += camino(padre, muelle)[1:]
        orden.append(muelle)
    return recorrido, orden
