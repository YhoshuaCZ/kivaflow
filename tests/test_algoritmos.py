"""Cada algoritmo, comparado con NetworkX (oráculo) y con casos chicos resueltos a mano."""
import random

import networkx as nx
import pytest

from kivaflow import bellman_ford as bf
from kivaflow import config, edmonds_karp as ek, grafo, pedido
from kivaflow.bfs import bfs, bfs_distancias

NODOS = grafo.leer_nodos()
ARISTAS = grafo.leer_aristas()
ADY = grafo.adyacencia(ARISTAS, "punta")
DIRIGIDAS = grafo.lista_de_aristas(ADY)


def nx_grafo(perfil="punta"):
    g = nx.Graph()
    for a in ARISTAS:
        g.add_edge(a["Nodo_Origen"], a["Nodo_Destino"], weight=grafo.peso(a, perfil))
    return g


# ---------- BFS ----------

def test_bfs_a_mano():
    #  A - B - C
    #  |       |
    #  D ----- E      A->C: 2 pasillos por arriba (por abajo serían 3)
    ady = {"A": [("B", 1), ("D", 1)], "B": [("A", 1), ("C", 1)], "C": [("B", 1), ("E", 1)],
           "D": [("A", 1), ("E", 1)], "E": [("D", 1), ("C", 1)]}
    camino, _ = bfs(ady, "A", "C")
    assert camino == ["A", "B", "C"]
    assert bfs(ady, "A", "Z") == ([], 5)               # inalcanzable: recorrió todo


def test_bfs_igual_que_networkx():
    g = nx_grafo()
    rng = random.Random(1)
    for _ in range(20):
        s, t = rng.sample(sorted(NODOS), 2)
        camino, _ = bfs(ADY, s, t)
        assert len(camino) - 1 == nx.shortest_path_length(g, s, t)
        assert all(g.has_edge(u, v) for u, v in zip(camino, camino[1:]))
    assert bfs_distancias(ADY, "22-00") == nx.single_source_shortest_path_length(g, "22-00")


def test_bfs_con_varios_destinos_para_en_el_mas_cercano():
    destinos = {"00-05", "00-02", "10-10"}
    camino, visitados = bfs(ADY, "00-00", destinos)
    assert camino[-1] == "00-02"
    assert visitados < len(NODOS)                        # no exploró todo el almacén


# ---------- Bellman-Ford ----------

def test_bellman_ford_a_mano_con_arista_negativa():
    nodos = ["s", "a", "b", "t"]
    aristas = [("s", "a", 4), ("s", "b", 5), ("b", "a", -3), ("a", "t", 2)]
    camino, costo, _ = bf.ruta(nodos, aristas, "s", "t")
    assert camino == ["s", "b", "a", "t"] and costo == 4      # 5 - 3 + 2


def test_bellman_ford_detecta_ciclo_negativo():
    nodos = ["s", "a", "b"]
    aristas = [("s", "a", 1), ("a", "b", -2), ("b", "a", 1)]
    with pytest.raises(bf.CicloNegativo):
        bf.bellman_ford(nodos, aristas, "s")


@pytest.mark.parametrize("perfil", ["punta", "valle"])
def test_bellman_ford_igual_que_networkx(perfil):
    ady = grafo.adyacencia(ARISTAS, perfil)
    dist, _, stats = bf.bellman_ford(ady.keys(), grafo.lista_de_aristas(ady), "22-39")
    esperado = nx.single_source_bellman_ford_path_length(nx_grafo(perfil), "22-39")
    assert all(abs(dist[n] - esperado[n]) < 1e-9 for n in NODOS)
    assert stats["rondas"] < len(NODOS) - 1                    # la salida anticipada funcionó


def test_bellman_ford_evita_congestion_y_bfs_no():
    # Costo ajustado de la ruta de Bellman-Ford <= costo ajustado de la ruta de BFS.
    rng = random.Random(2)
    aristas_por_par = {frozenset((a["Nodo_Origen"], a["Nodo_Destino"])): a for a in ARISTAS}
    for _ in range(10):
        s, t = rng.sample(sorted(NODOS), 2)
        c_bfs, _ = bfs(ADY, s, t)
        c_bf, costo, _ = bf.ruta(ADY.keys(), DIRIGIDAS, s, t)
        assert abs(pedido.medir(c_bf, aristas_por_par)["distancia_ajustada_m"] - round(costo, 2)) < 0.02
        assert costo <= pedido.medir(c_bfs, aristas_por_par)["distancia_ajustada_m"] + 1e-6


# ---------- Edmonds-Karp ----------

def test_edmonds_karp_a_mano():
    # Ejemplo clásico de red de flujo (Cormen et al., 2022, cap. 24): flujo máximo 23.
    cap = {"s": {"v1": 16, "v2": 13}, "v1": {"v3": 12}, "v2": {"v1": 4, "v4": 14},
           "v3": {"v2": 9, "t": 20}, "v4": {"v3": 7, "t": 4}}
    valor, flujo, stats = ek.flujo_maximo(cap, "s", "t")
    assert valor == 23
    corte = ek.corte_minimo(cap, stats["lado_fuente"])
    assert sum(c for _, _, c in corte) == 23                    # flujo máximo = corte mínimo
    for u, vec in flujo.items():                                # respeta capacidades
        for v, f in vec.items():
            assert 0 < f <= cap[u][v]


def test_edmonds_karp_entre_zonas_igual_que_networkx():
    cap = grafo.capacidades(ARISTAS)
    valor, _, cuellos, _ = ek.entre_zonas(cap, NODOS, "Recepción y Almacenamiento", "Empaque y Despacho")
    g = nx.DiGraph()
    for u, vec in cap.items():
        for v, c in vec.items():
            g.add_edge(u, v, capacity=c)
    for n, d in NODOS.items():
        if d["Zona"] == "Recepción y Almacenamiento":
            g.add_edge("S", n)                                  # sin capacity = infinita
        if d["Zona"] == "Empaque y Despacho":
            g.add_edge(n, "T")
    assert valor == nx.maximum_flow_value(g, "S", "T")
    assert sum(c for _, _, c in cuellos) == valor
    assert valor <= config.FILAS * max(config.CAPACIDAD_OPERARIOS_MIN.values())


# ---------- Ruta de un pedido ----------

def test_ruta_de_pedido_visita_todo_y_vuelve():
    racks = [n for n, d in NODOS.items() if d["Tipo"] == "rack"]
    rng = random.Random(3)
    elegidos = rng.sample(racks, 5)
    for estrategia in ("bfs", "bellman_ford"):
        r = pedido.ruta_pedido(ADY, DIRIGIDAS, "22-39", elegidos, estrategia)
        assert r["camino"][0] == r["camino"][-1] == "22-39"
        assert sorted(r["orden"]) == sorted(elegidos)
        assert set(elegidos) <= set(r["camino"])
        assert r["busquedas"] == 6
