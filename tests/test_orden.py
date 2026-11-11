"""Orden de visita óptimo (Held-Karp): contra la fuerza bruta y contra el voraz."""
import random
import sys
from itertools import permutations
from pathlib import Path

import pytest

sys.path[:0] = [str(Path(__file__).resolve().parent.parent / "scripts")]

from kivaflow.orden import MAX_PRODUCTOS, held_karp, ruta_optima  # noqa: E402
from kivaflow.pedido import Buscador, ruta_pedido  # noqa: E402


def _costo(orden, d_origen, d, d_final):
    return d_origen[orden[0]] + sum(d[a][b] for a, b in zip(orden, orden[1:])) + d_final[orden[-1]]


@pytest.mark.parametrize("semilla", range(40))
def test_held_karp_igual_a_probar_todos_los_ordenes(semilla):
    rng = random.Random(semilla)
    n = rng.randint(1, 7)
    d_origen = [rng.randint(1, 30) for _ in range(n)]
    d = [[0 if i == j else rng.randint(1, 30) for j in range(n)] for i in range(n)]  # ni siquiera simétrica
    d_final = [rng.randint(0, 30) for _ in range(n)]
    orden, costo, estados = held_karp(d_origen, d, d_final)
    assert sorted(orden) == list(range(n))  # visita cada producto una vez
    assert costo == _costo(orden, d_origen, d, d_final)  # el costo es el del orden que devuelve
    assert costo == min(_costo(p, d_origen, d, d_final) for p in permutations(range(n)))
    assert estados == n * 2 ** (n - 1)  # los estados (S, j) con j en S


def test_held_karp_caso_a_mano():
    # Productos en una línea: origen en 0, A en 1, B en 10 y C en 2. Sin cierre conviene A, C, B = 10.
    # Si cerrar el recorrido solo es barato desde A, hay que ir hasta B y volver: termina en A y cuesta 19.
    d_origen = [1, 10, 2]
    d = [[0, 9, 1], [9, 0, 8], [1, 8, 0]]
    assert held_karp(d_origen, d)[:2] == ([0, 2, 1], 10)
    orden, costo, _ = held_karp(d_origen, d, d_final=[0, 50, 50])
    assert orden[-1] == 0 and costo == 19


def test_held_karp_pedido_vacio():
    assert held_karp([], []) == ([], 0.0, 0)


def test_ruta_optima_en_el_almacen_nunca_pierde_contra_el_voraz():
    import app
    a = app.Almacen()
    hubo_mejora = False
    for semilla in range(6):
        productos = a.pedido_al_azar(5, semilla=semilla)
        voraz, rec_v = a.ruta("Bellman-Ford", "02-00", productos, orden="voraz", repeticiones=1)
        optimo, rec_o = a.ruta("Bellman-Ford", "02-00", productos, orden="óptimo", repeticiones=1)
        mv, mo = (float(m.resultado["metros ajustados"][:-2]) for m in (voraz, optimo))
        assert mo <= mv + 1e-9
        hubo_mejora |= mo < mv - 0.01
        assert set(productos) <= set(rec_o) and rec_o[0] == "02-00" and rec_o[-1] in a.muelles_despacho
        assert all((u, v) in a.d.nivel for u, v in zip(rec_o, rec_o[1:]))  # cada paso es un pasillo real
        assert optimo.operaciones["estados de la DP (n · 2ⁿ⁻¹)"] == 5 * 2 ** 4
    assert hubo_mejora  # en alguno de los pedidos el voraz no era óptimo


def test_ruta_optima_sin_muelle_y_con_un_producto():
    import app
    a = app.Almacen()
    b = Buscador(a.d.nodos, a.arcos["BFS"], "BFS")
    rec, orden = ruta_optima(b, "02-00", ["10-10"])
    assert orden == ["10-10"] and rec == ruta_pedido(Buscador(a.d.nodos, a.arcos["BFS"], "BFS"), "02-00", ["10-10"])[0]
    assert ruta_optima(b, "02-00", []) == (["02-00"], [])


def test_ruta_optima_rechaza_pedidos_grandes():
    import app
    a = app.Almacen()
    b = Buscador(a.d.nodos, a.arcos["BFS"], "BFS")
    with pytest.raises(ValueError):
        ruta_optima(b, "02-00", a.racks[:MAX_PRODUCTOS + 1])


def test_experimento_compara_las_tres_estrategias(monkeypatch):
    import app
    import experimento
    monkeypatch.setattr(experimento, "TAMANOS", (3,))
    filas = experimento.correr(app.Almacen(), 2)
    assert len(filas) == 2 * 3
    t = experimento.resumir(filas)[0]
    bfs, bf, opt = (e[0] for e in experimento.ESTRATEGIAS)
    assert t[opt] <= t[bf] <= t[bfs]  # cada decisión ahorra (o empata) caminata
