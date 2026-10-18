"""Comprueba que el dataset cumple lo que dice el informe y lo que pide el enunciado."""
import csv
import random
import subprocess
import sys
from collections import Counter
from pathlib import Path

import networkx as nx

from kivaflow import config, demanda, grafo, layout, trafico

RAIZ = Path(__file__).resolve().parent.parent


def test_tamano_minimo_del_enunciado():
    # El enunciado pide >= 1500 nodos (500 por integrante).
    nodos = layout.construir_nodos()
    assert len(nodos) == 1800
    assert Counter(n.zona for n in nodos) == {
        "Recepción y Almacenamiento": 585, "Picking": 630, "Empaque y Despacho": 585,
    }
    assert all(c >= 500 for c in Counter(n.zona for n in nodos).values())


def test_aristas_de_la_cuadricula():
    aristas = layout.construir_aristas()
    assert len(aristas) == 3515
    assert len({frozenset((a.origen, a.destino)) for a in aristas}) == 3515  # sin duplicados


def test_csv_conexo_y_sin_aislados():
    nodos = grafo.leer_nodos()
    aristas = grafo.leer_aristas()
    g = nx.Graph()
    g.add_nodes_from(nodos)
    g.add_edges_from((a["Nodo_Origen"], a["Nodo_Destino"]) for a in aristas)
    assert g.number_of_nodes() == 1800 and g.number_of_edges() == 3515
    assert nx.is_connected(g)
    assert not list(nx.isolates(g))


def test_pesos_coherentes():
    for a in grafo.leer_aristas():
        factor = config.FACTOR_CONGESTION[a["Frecuencia_Pedidos"]]
        d, adj, t = float(a["Distancia_m"]), float(a["Distancia_Ajustada_m"]), float(a["Tiempo_Estimado_s"])
        assert d > 0 and abs(adj - d * factor) < 1e-3
        assert abs(t - adj / config.VELOCIDAD_M_S) < 1e-2


def test_cada_rack_tiene_un_sku_distinto():
    nodos = grafo.leer_nodos().values()
    skus = [n["SKU"] for n in nodos if n["Tipo"] == "rack"]
    assert all(skus) and len(set(skus)) == len(skus)
    assert not any(n["SKU"] for n in nodos if n["Tipo"] == "estacion")


def test_dataset_reproducible(tmp_path):
    subprocess.run([sys.executable, str(RAIZ / "scripts/generar_dataset.py"), "--salida", str(tmp_path)],
                   check=True, capture_output=True)
    for nombre in ("nodos.csv", "aristas.csv", "skus.csv"):
        assert (tmp_path / nombre).read_bytes() == (RAIZ / "data" / nombre).read_bytes()


def test_instacart_con_archivo_chico(tmp_path):
    # Mismo formato que order_products__prior.csv de Kaggle, agrupado por order_id.
    filas = [("1", "10"), ("1", "20"), ("2", "10"), ("3", "30"), ("3", "10"), ("4", "99")]
    with open(tmp_path / "order_products__prior.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["order_id", "product_id", "add_to_cart_order", "reordered"])
        for i, (o, p) in enumerate(filas):
            w.writerow([o, p, i, 0])
    popularidad, pedidos = demanda.instacart(tmp_path, n_skus=2, rng=random.Random(0))
    assert popularidad[0] == ("IC10", 3)              # el más pedido primero
    assert len(popularidad) == 2 and popularidad[1][1] == 1  # empate 20/30: entra uno de los dos
    assert all(p for p in pedidos)                    # el pedido 4 (solo producto 99) se descarta
    assert len(pedidos) == 3


def test_simulacion_usa_rutas_validas():
    nodos = layout.construir_nodos()
    aristas = {frozenset((a.origen, a.destino)) for a in layout.construir_aristas()}
    popularidad, pedidos = demanda.sinteticos(sum(n.tipo == "rack" for n in nodos), random.Random(1))
    trafico.asignar_skus(nodos, popularidad, random.Random(1))
    uso = trafico.simular(nodos, pedidos[:50], random.Random(1))
    assert uso and set(uso) <= aristas                # solo cruza pasillos que existen
