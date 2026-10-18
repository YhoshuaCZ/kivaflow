"""Mide cuánto se usa cada pasillo simulando pedidos sobre la cuadrícula.

Esto NO es uno de los algoritmos del trabajo (BFS, Bellman-Ford, Edmonds-Karp):
solo sirve para darle a cada arista una `Frecuencia_Pedidos` medida en vez de al azar.
Como en una cuadrícula sin obstáculos el camino más corto es un camino en L
(primero por la columna, luego por la fila), no hace falta un algoritmo de grafos.
"""
import random
from collections import Counter

from . import config
from .layout import id_nodo


def asignar_skus(nodos, popularidad, rng):
    """Un SKU por rack, en posición aleatoria (asignación base, sin optimizar)."""
    racks = [n for n in nodos if n.tipo == "rack"]
    skus = [s for s, _ in popularidad]
    rng.shuffle(skus)
    for rack, sku in zip(racks, skus):
        rack.sku = sku


def _camino_l(a, b):
    """Aristas (como pares ordenados de ids) del camino en L de a hasta b."""
    (f, c), (f2, c2) = a, b
    pasos = []
    while f != f2:
        nf = f + (1 if f2 > f else -1)
        pasos.append((id_nodo(f, c), id_nodo(nf, c)))
        f = nf
    while c != c2:
        nc = c + (1 if c2 > c else -1)
        pasos.append((id_nodo(f, c), id_nodo(f, nc)))
        c = nc
    return pasos


def simular(nodos, pedidos, rng=None):
    """Cada pedido sale de un muelle de despacho, visita sus racks y vuelve.

    Devuelve un Counter {frozenset({u, v}): veces que se cruzó la arista}.
    """
    rng = rng or random.Random(config.SEMILLA)
    pos = {n.sku: (n.fila, n.col) for n in nodos if n.sku}
    muelles = [(n.fila, n.col) for n in nodos if n.tipo == "estacion" and n.col == config.COLUMNAS - 1]
    uso = Counter()
    for pedido in pedidos:
        inicio = rng.choice(muelles)
        # recorrido simple: de la columna más lejana a la más cercana al despacho
        paradas = sorted((pos[s] for s in pedido if s in pos), key=lambda p: (p[1], p[0]))
        actual = inicio
        for parada in paradas + [inicio]:
            for u, v in _camino_l(actual, parada):
                uso[frozenset((u, v))] += 1
            actual = parada
    return uso


def niveles(pares, uso):
    """Baja/Media/Alta por terciles del tráfico medido.

    pares: [(origen, destino), ...] de cada pasillo; uso: Counter {frozenset({u, v}): cruces}.
    """
    valores = sorted(uso.get(frozenset(p), 0) for p in pares)
    t1 = valores[len(valores) // 3]
    t2 = valores[2 * len(valores) // 3]

    def nivel(x):
        return "Baja" if x <= t1 else "Media" if x <= t2 else "Alta"

    return {tuple(p): nivel(uso.get(frozenset(p), 0)) for p in pares}
