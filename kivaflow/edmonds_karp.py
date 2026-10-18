"""Edmonds-Karp: flujo máximo y cuellos de botella entre dos zonas del almacén.

Es Ford-Fulkerson eligiendo siempre el camino de aumento más corto (en aristas),
que se encuentra con BFS sobre la red residual:
1. Buscar con BFS un camino fuente -> sumidero con capacidad residual > 0.
2. Empujar por él tanto flujo como su arista más estrecha permita.
3. Actualizar la red residual (restar en el sentido del camino, sumar al revés).
4. Repetir hasta que no haya camino.

Al terminar, los nodos que el BFS todavía alcanza desde la fuente forman un lado del
CORTE MÍNIMO; las aristas que salen de ese lado están saturadas y son los cuellos de
botella (teorema de flujo máximo-corte mínimo: su capacidad total = flujo máximo).

Complejidad: O(V · E²) tiempo, O(V + E) memoria. En la práctica son
(flujo máximo / capacidad del camino) búsquedas BFS de O(V + E) cada una.
"""
from collections import deque

FUENTE = "__fuente__"
SUMIDERO = "__sumidero__"


def _camino_aumento(residual, s, t):
    padre = {s: None}
    cola = deque([s])
    while cola:
        u = cola.popleft()
        for v, c in residual[u].items():
            if c > 0 and v not in padre:
                padre[v] = u
                if v == t:
                    return padre
                cola.append(v)
    return None


def flujo_maximo(capacidad, s, t, pasos=None):
    """capacidad: {u: {v: c}}. Devuelve (valor, flujo, stats).

    flujo[u][v] > 0 es lo que pasa de u a v. stats = {"caminos_aumento", "lado_fuente"}.
    Si se pasa una lista en `pasos`, se anota (camino, delta) por cada camino de
    aumento (para la animación). No cambia el resultado.
    """
    residual = {u: dict(vec) for u, vec in capacidad.items()}
    for u, vec in capacidad.items():
        for v in vec:
            residual.setdefault(v, {}).setdefault(u, 0)
    residual.setdefault(s, {})
    residual.setdefault(t, {})

    valor = caminos = 0
    while (padre := _camino_aumento(residual, s, t)) is not None:
        caminos += 1
        # cuello del camino
        delta, v = float("inf"), t
        while padre[v] is not None:
            u = padre[v]
            delta = min(delta, residual[u][v])
            v = u
        if pasos is not None:
            camino, x = [], t
            while x is not None:
                camino.append(x)
                x = padre[x]
            pasos.append((camino[::-1], delta))
        # actualizar red residual
        v = t
        while padre[v] is not None:
            u = padre[v]
            residual[u][v] -= delta
            residual[v][u] += delta
            v = u
        valor += delta

    flujo = {}
    for u, vec in capacidad.items():
        for v, c in vec.items():
            f = c - residual[u][v]
            if f > 0:
                flujo.setdefault(u, {})[v] = f
    lado_fuente = _alcanzables(residual, s)
    return valor, flujo, {"caminos_aumento": caminos, "lado_fuente": lado_fuente}


def _alcanzables(residual, s):
    vistos = {s}
    cola = deque([s])
    while cola:
        u = cola.popleft()
        for v, c in residual[u].items():
            if c > 0 and v not in vistos:
                vistos.add(v)
                cola.append(v)
    return vistos


def corte_minimo(capacidad, lado_fuente):
    """Aristas (u, v, capacidad) que cruzan del lado de la fuente al otro: los cuellos de botella."""
    return [(u, v, c) for u in lado_fuente for v, c in capacidad.get(u, {}).items() if v not in lado_fuente]


def entre_zonas(capacidad, nodos, zona_origen, zona_destino, pasos=None):
    """Flujo máximo desde toda una zona hasta otra.

    Se agrega una superfuente unida a cada nodo de `zona_origen` y un supersumidero
    al que llega cada nodo de `zona_destino`, con capacidad "infinita", para que el
    límite lo pongan solo los pasillos.
    """
    infinito = sum(c for vec in capacidad.values() for c in vec.values())
    cap = {u: dict(vec) for u, vec in capacidad.items()}
    cap[FUENTE] = {n: infinito for n, d in nodos.items() if d["Zona"] == zona_origen}
    for n, d in nodos.items():
        if d["Zona"] == zona_destino:
            cap.setdefault(n, {})[SUMIDERO] = infinito
    valor, flujo, stats = flujo_maximo(cap, FUENTE, SUMIDERO, pasos)
    cuellos = [(u, v, c) for u, v, c in corte_minimo(cap, stats["lado_fuente"]) if FUENTE not in (u, v) and SUMIDERO not in (u, v)]
    return valor, flujo, cuellos, stats
