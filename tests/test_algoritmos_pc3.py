"""Pruebas de los algoritmos de la demo de la PC3: casos a mano y contra NetworkX."""
import random

import networkx as nx
import pytest

from kivaflow.caminos import bellman_ford, camino, camino_fw, floyd_warshall
from kivaflow.flujo import FUENTE, SUMIDERO, ford_fulkerson
from kivaflow.mochila import mochila_01
from kivaflow.mst import es_arbol_de_expansion, fuerza_bruta, kruskal, prim


def _grilla(f, c, semilla):
    rng = random.Random(semilla)
    nodos = [(i, j) for i in range(f) for j in range(c)]
    aristas = []
    for i, j in nodos:
        if i + 1 < f:
            aristas.append(((i, j), (i + 1, j), rng.choice([1.2, 1.5, 1.92])))
        if j + 1 < c:
            aristas.append(((i, j), (i, j + 1), rng.choice([1.2, 1.5, 1.92])))
    return nodos, aristas


# ---- MST por fuerza bruta (hoja 10) ----

@pytest.mark.parametrize("semilla", [1, 2, 3])
def test_fuerza_bruta_igual_a_kruskal_y_prim(semilla):
    nodos, aristas = _grilla(3, 3, semilla)
    fb = fuerza_bruta(nodos, aristas)
    assert es_arbol_de_expansion(nodos, fb.aristas)
    assert fb.costo == pytest.approx(kruskal(nodos, aristas).costo)
    assert fb.costo == pytest.approx(prim(nodos, aristas).costo)


# ---- Ford-Fulkerson (hoja 11) ----

def _red(arcos):
    cap = {}
    for u, v, c in arcos:
        cap.setdefault(u, {}).setdefault(v, 0)
        cap.setdefault(v, {}).setdefault(u, 0)
        cap[u][v] += c
    return cap


def test_ford_fulkerson_caso_de_clase():
    # Red clásica de CLRS: flujo máximo 23.
    arcos = [("s", "a", 16), ("s", "c", 13), ("a", "b", 12), ("c", "a", 4), ("b", "c", 9),
             ("c", "d", 14), ("d", "b", 7), ("b", "t", 20), ("d", "t", 4)]
    f = ford_fulkerson(_red(arcos), "s", "t")
    assert f.valor == 23
    assert sum(c for *_, c in f.corte) == 23  # flujo máximo = corte mínimo


@pytest.mark.parametrize("semilla", [4, 5])
def test_ford_fulkerson_contra_networkx(semilla):
    nodos, aristas = _grilla(5, 6, semilla)
    capacidad = {1.2: 3, 1.5: 2, 1.92: 1}
    arcos = []
    for u, v, w in aristas:
        arcos += [(u, v, capacidad[w]), (v, u, capacidad[w])]
    fuentes = [(i, 0) for i in range(5)]
    sumideros = [(i, 5) for i in range(5)]
    arcos += [(FUENTE, s, float("inf")) for s in fuentes] + [(t, SUMIDERO, float("inf")) for t in sumideros]
    g = nx.DiGraph()
    for u, v, c in arcos:
        g.add_edge(u, v, capacity=c)
    f = ford_fulkerson(_red(arcos))
    assert f.valor == nx.maximum_flow_value(g, FUENTE, SUMIDERO)
    assert sum(c for *_, c in f.corte) == f.valor


# ---- Bellman-Ford y Floyd-Warshall (hoja 13) ----

def test_bellman_ford_contra_dijkstra():
    nodos, aristas = _grilla(6, 6, 7)
    arcos = [(u, v, w) for u, v, w in aristas] + [(v, u, w) for u, v, w in aristas]
    bf = bellman_ford(nodos, arcos, (0, 0))
    g = nx.Graph()
    g.add_weighted_edges_from(aristas)
    esperado = nx.single_source_dijkstra_path_length(g, (0, 0))
    for n in nodos:
        assert bf.dist[n] == pytest.approx(esperado[n])
    assert not bf.ciclo_negativo
    c = camino(bf.padre, (5, 5))
    assert c[0] == (0, 0) and c[-1] == (5, 5)


def test_bellman_ford_detecta_ciclo_negativo():
    arcos = [("a", "b", 1), ("b", "c", -2), ("c", "a", -1), ("c", "d", 3)]
    assert bellman_ford("abcd", arcos, "a").ciclo_negativo


def test_bellman_ford_peso_negativo_sin_ciclo():
    arcos = [("a", "b", 4), ("a", "c", 2), ("c", "b", -3), ("b", "d", 1)]
    bf = bellman_ford("abcd", arcos, "a")
    assert bf.dist["b"] == -1 and bf.dist["d"] == 0 and not bf.ciclo_negativo


def test_floyd_warshall_igual_a_bellman_ford():
    nodos, aristas = _grilla(4, 4, 8)
    arcos = [(u, v, w) for u, v, w in aristas] + [(v, u, w) for u, v, w in aristas]
    orden, dist, sig = floyd_warshall(nodos, arcos)
    for o in [(0, 0), (2, 3)]:
        bf = bellman_ford(nodos, arcos, o)
        i = orden.index(o)
        for j, n in enumerate(orden):
            assert dist[i][j] == pytest.approx(bf.dist[n])
    c = camino_fw(orden, sig, (0, 0), (3, 3))
    peso = {(u, v): w for u, v, w in arcos}
    assert sum(peso[p] for p in zip(c, c[1:])) == pytest.approx(dist[0][orden.index((3, 3))])


# ---- Mochila 0/1 (módulo 12) ----

def test_mochila_caso_a_mano():
    valor, elegidos, _ = mochila_01([1, 3, 4, 5], [1, 4, 5, 7], 7)
    assert valor == 9 and elegidos == [1, 2]


def test_mochila_contra_fuerza_bruta():
    from itertools import combinations
    rng = random.Random(9)
    pesos = [rng.randint(1, 8) for _ in range(9)]
    valores = [rng.randint(1, 10) for _ in range(9)]
    W = 15
    mejor = max(sum(valores[i] for i in s) for r in range(10) for s in combinations(range(9), r)
                if sum(pesos[i] for i in s) <= W)
    valor, elegidos, _ = mochila_01(pesos, valores, W)
    assert valor == mejor
    assert sum(pesos[i] for i in elegidos) <= W and sum(valores[i] for i in elegidos) == valor
