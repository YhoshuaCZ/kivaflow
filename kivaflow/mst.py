"""Árbol de expansión mínima (MST) con Kruskal y con Prim, programados a mano.

En KivaFlow el MST es la «red de servicio»: los V - 1 pasillos que conectan las
1800 ubicaciones con la menor distancia ajustada por congestión.

Los dos devuelven un `Resultado` con las aristas en el orden en que se eligieron,
para poder dibujar cómo crece el árbol.
"""
import heapq
from dataclasses import dataclass, field

from kivaflow.ufds import UFDS


@dataclass
class Resultado:
    algoritmo: str
    aristas: list = field(default_factory=list)  # [(u, v, peso), ...] en orden de elección
    costo: float = 0.0
    revisadas: int = 0  # Kruskal: aristas ordenadas que miró · Prim: entradas sacadas del heap
    descartadas: int = 0  # aristas que habrían formado ciclo (o entradas viejas del heap)


def lista_aristas(aristas_csv, peso="Distancia_Ajustada_m"):
    """[(u, v, peso)] desde las filas de aristas.csv."""
    return [(a["Nodo_Origen"], a["Nodo_Destino"], float(a[peso])) for a in aristas_csv]


def kruskal(nodos, aristas):
    """Kruskal: ordena los pasillos de menor a mayor y agrega los que no forman ciclo.

    O(E log E) por el ordenamiento; cada `unir` cuesta casi O(1) amortizado.
    Empates: se desempatan por (u, v) para que el resultado sea reproducible.
    """
    r = Resultado("Kruskal")
    uf = UFDS(nodos)
    objetivo = len(uf.padre) - 1
    for u, v, w in sorted(aristas, key=lambda a: (a[2], a[0], a[1])):
        r.revisadas += 1
        if uf.unir(u, v):
            r.aristas.append((u, v, w))
            r.costo += w
            if len(r.aristas) == objetivo:  # el árbol ya está completo
                break
        else:
            r.descartadas += 1
    return r


def prim(nodos, aristas, inicio=None):
    """Prim: hace crecer un solo árbol desde `inicio`, agregando siempre el pasillo
    más barato que sale del árbol. Con heap binario: O(E log V).
    """
    ady = {n: [] for n in nodos}
    for u, v, w in aristas:
        ady[u].append((v, w))
        ady[v].append((u, w))
    inicio = inicio if inicio is not None else min(ady)
    r = Resultado("Prim")
    en_arbol = {inicio}
    heap = [(w, inicio, v) for v, w in ady[inicio]]
    heapq.heapify(heap)
    objetivo = len(ady) - 1
    while heap and len(r.aristas) < objetivo:
        w, u, v = heapq.heappop(heap)
        r.revisadas += 1
        if v in en_arbol:  # entrada vieja: v ya entró por un pasillo más barato
            r.descartadas += 1
            continue
        en_arbol.add(v)
        r.aristas.append((u, v, w))
        r.costo += w
        for x, w2 in ady[v]:
            if x not in en_arbol:
                heapq.heappush(heap, (w2, v, x))
    return r


def es_arbol_de_expansion(nodos, aristas_arbol):
    """V - 1 aristas y sin ciclos (con UFDS) => conecta todo y es un árbol."""
    nodos = list(nodos)
    if len(aristas_arbol) != len(nodos) - 1:
        return False
    uf = UFDS(nodos)
    return all(uf.unir(u, v) for u, v, _ in aristas_arbol) and uf.grupos == 1
