"""Simulación de un turno: varios operarios trabajan a la vez y se forma la congestión.

1. Cada operario recibe un pedido (productos según la popularidad), sale de un muelle
   de despacho, recoge en sus racks y vuelve. Su ruta la calcula BFS o Bellman-Ford.
2. Se cuenta cuántas veces se cruza cada pasillo → congestión Baja/Media/Alta por
   terciles (lo mismo que se hizo para el dataset, pero con este turno).
3. Con esa congestión cambia la capacidad de los pasillos y Edmonds-Karp calcula el
   flujo máximo de Recepción a Despacho y sus cuellos de botella.

Así se ve la cadena completa: demanda → rutas → tráfico → congestión → capacidad.
"""
import random
from collections import Counter

from . import edmonds_karp as ek
from . import grafo, pedido, trafico


def turno(nodos, ady, dirigidas, popularidad, n_operarios, max_productos, estrategia, semilla):
    """Devuelve la lista de operarios: {"muelle", "racks", "camino"}."""
    rng = random.Random(semilla)
    operarios = []
    for _ in range(n_operarios):
        muelle, racks = pedido.aleatorio(nodos, popularidad, rng.randint(1, max_productos), rng)
        r = pedido.ruta_pedido(ady, dirigidas, muelle, racks, estrategia)
        operarios.append({"muelle": muelle, "racks": racks, "camino": r["camino"]})
    return operarios


def uso_hasta(operarios, t):
    """Cruces de cada pasillo considerando solo los primeros t pasos de cada operario."""
    uso = Counter()
    for op in operarios:
        c = op["camino"][: t + 1]
        for u, v in zip(c, c[1:]):
            uso[frozenset((u, v))] += 1
    return uso


def posicion(op, t):
    """Dónde está un operario en el paso t (se queda en el muelle cuando termina)."""
    c = op["camino"]
    return c[min(t, len(c) - 1)]


def congestion_y_flujo(nodos, aristas, operarios, zona_origen, zona_destino, pasos_flujo=None):
    """Congestión que dejó el turno y flujo máximo entre dos zonas con esa congestión."""
    pares = [(a["Nodo_Origen"], a["Nodo_Destino"]) for a in aristas]
    uso = uso_hasta(operarios, max(len(op["camino"]) for op in operarios))
    niveles = trafico.niveles(pares, uso)
    cap = grafo.capacidades(aristas, niveles)
    valor, _, cuellos, stats = ek.entre_zonas(cap, nodos, zona_origen, zona_destino, pasos_flujo)
    return {"uso": uso, "niveles": niveles, "valor": valor, "cuellos": cuellos, "stats": stats}
