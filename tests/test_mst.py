import networkx as nx
import pytest

from kivaflow import grafo
from kivaflow.mst import es_arbol_de_expansion, kruskal, lista_aristas, prim
from kivaflow.ufds import UFDS

# Grafo chico resuelto a mano (5 nodos, 7 aristas).
#   A-B 1, B-C 2, A-C 3, C-D 4, B-D 5, D-E 6, C-E 7
# Kruskal: A-B (1), B-C (2), A-C cerraría ciclo, C-D (4), B-D ciclo, D-E (6) -> costo 13.
CHICO_NODOS = list("ABCDE")
CHICO = [("A", "B", 1), ("B", "C", 2), ("A", "C", 3), ("C", "D", 4),
         ("B", "D", 5), ("D", "E", 6), ("C", "E", 7)]


def test_ufds_detecta_ciclo():
    uf = UFDS("abc")
    assert uf.unir("a", "b")
    assert uf.unir("b", "c")
    assert not uf.unir("a", "c")
    assert uf.grupos == 1


def test_kruskal_a_mano():
    r = kruskal(CHICO_NODOS, CHICO)
    assert [(u, v) for u, v, _ in r.aristas] == [("A", "B"), ("B", "C"), ("C", "D"), ("D", "E")]
    assert r.costo == 13
    assert r.descartadas == 2  # A-C y B-D


def test_prim_a_mano():
    r = prim(CHICO_NODOS, CHICO, inicio="A")
    assert r.costo == 13
    assert es_arbol_de_expansion(CHICO_NODOS, r.aristas)


@pytest.fixture(scope="module")
def almacen():
    return list(grafo.leer_nodos()), lista_aristas(grafo.leer_aristas())


def test_almacen_mismo_costo_que_networkx(almacen):
    nodos, aristas = almacen
    g = nx.Graph()
    g.add_weighted_edges_from(aristas)
    esperado = nx.minimum_spanning_tree(g).size(weight="weight")
    k, p = kruskal(nodos, aristas), prim(nodos, aristas)
    assert k.costo == pytest.approx(esperado)
    assert p.costo == pytest.approx(esperado)  # misma cota: propiedad del corte


def test_almacen_es_arbol(almacen):
    nodos, aristas = almacen
    for r in (kruskal(nodos, aristas), prim(nodos, aristas)):
        assert len(r.aristas) == 1799
        assert es_arbol_de_expansion(nodos, r.aristas)
