"""Los pasos que anotan los algoritmos (para las animaciones) son fieles y no cambian el resultado."""
from collections import Counter

from kivaflow import bellman_ford as bf
from kivaflow import edmonds_karp as ek
from kivaflow import grafo, interactivo, pedido, simulacion
from kivaflow.bfs import bfs, bfs_distancias

NODOS = grafo.leer_nodos()
ARISTAS = grafo.leer_aristas()
ADY = grafo.adyacencia(ARISTAS, "punta")
DIRIGIDAS = grafo.lista_de_aristas(ADY)
POP, _ = grafo.leer_popularidad()


def test_pasos_de_bfs_son_los_niveles_reales():
    pasos = []
    camino, visitados = bfs(ADY, "22-39", "00-00", pasos)
    assert camino == bfs(ADY, "22-39", "00-00")[0]          # registrar no cambia el resultado
    assert len(pasos) == visitados
    dist = bfs_distancias(ADY, "22-39")
    assert all(dist[u] == nivel for u, nivel in pasos)      # el nivel anotado es la distancia en pasillos
    assert [n for _, n in pasos] == sorted(n for _, n in pasos)  # FIFO: los niveles nunca retroceden


def test_pasos_de_bellman_ford_son_las_rondas():
    pasos = []
    dist, _, stats = bf.bellman_ford(ADY.keys(), DIRIGIDAS, "22-39", pasos)
    assert len(pasos) == stats["rondas"]
    assert pasos[-1] == []                                  # la última ronda no mejoró nada (salida anticipada)
    assert dist == bf.bellman_ford(ADY.keys(), DIRIGIDAS, "22-39")[0]


def test_pasos_de_edmonds_karp_suman_el_flujo():
    pasos = []
    cap = grafo.capacidades(ARISTAS)
    valor, _, cuellos, stats = ek.entre_zonas(cap, NODOS, "Recepción y Almacenamiento", "Empaque y Despacho", pasos)
    assert len(pasos) == stats["caminos_aumento"]
    assert sum(delta for _, delta in pasos) == valor
    assert all(c[0] == ek.FUENTE and c[-1] == ek.SUMIDERO for c, _ in pasos)
    assert [len(c) for c, _ in pasos] == sorted(len(c) for c, _ in pasos)  # BFS: caminos cada vez más largos


def test_ruta_sin_regresar_termina_en_un_destino():
    r = pedido.ruta_pedido(ADY, DIRIGIDAS, "00-00", ["10-10", "20-20"], "bfs", regresar=False)
    assert r["camino"][0] == "00-00" and r["camino"][-1] in {"10-10", "20-20"}
    assert r["busquedas"] == 2


def test_simulacion_reproducible_y_coherente():
    ops = simulacion.turno(NODOS, ADY, DIRIGIDAS, POP, 10, 3, "bfs", semilla=7)
    assert ops == simulacion.turno(NODOS, ADY, DIRIGIDAS, POP, 10, 3, "bfs", semilla=7)
    assert all(op["camino"][0] == op["camino"][-1] == op["muelle"] for op in ops)
    total = sum(len(op["camino"]) - 1 for op in ops)
    assert sum(simulacion.uso_hasta(ops, 10_000).values()) == total   # cada paso cruza un pasillo
    res = simulacion.congestion_y_flujo(NODOS, ARISTAS, ops, "Recepción y Almacenamiento", "Empaque y Despacho")
    assert sum(c for _, _, c in res["cuellos"]) == res["valor"]
    assert set(Counter(res["niveles"].values())) <= {"Baja", "Media", "Alta"}


def test_animaciones_se_arman():
    registro = []
    pedido.ruta_pedido(ADY, DIRIGIDAS, "22-39", ["05-05", "40-10"], "bellman_ford", registro)
    fig = interactivo.animacion_busqueda(NODOS, ARISTAS, registro, "bellman_ford", "22-39", ["05-05", "40-10"])
    assert 0 < len(fig.frames) <= 160
    assert "listo" in fig.frames[-1].layout.title.text
    ops = simulacion.turno(NODOS, ADY, DIRIGIDAS, POP, 5, 2, "bfs", semilla=1)
    assert len(interactivo.animacion_turno(NODOS, ARISTAS, ops).frames) <= 61
