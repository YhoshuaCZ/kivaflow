"""Pruebas de la ruta de un pedido, de la medición y del aplicativo (sin abrir ventana)."""
import sys
from pathlib import Path

import pytest

sys.path[:0] = [str(Path(__file__).resolve().parent.parent / "scripts")]

from kivaflow.medicion import Medicion, guardar_csv, medir, tabla  # noqa: E402
from kivaflow.pedido import Buscador, ruta_pedido  # noqa: E402


def _grilla(f, c):
    nodos = [f"{i:02d}-{j:02d}" for i in range(f) for j in range(c)]
    arcos = []
    for i in range(f):
        for j in range(c):
            for di, dj in ((1, 0), (0, 1)):
                if i + di < f and j + dj < c:
                    u, v = f"{i:02d}-{j:02d}", f"{i + di:02d}-{j + dj:02d}"
                    arcos += [(u, v, 1.0), (v, u, 1.0)]
    return nodos, arcos


@pytest.mark.parametrize("algoritmo", ["BFS", "Bellman-Ford"])
def test_ruta_pedido_visita_todo_y_termina_en_muelle(algoritmo):
    nodos, arcos = _grilla(5, 5)
    b = Buscador(nodos, arcos, algoritmo)
    rec, orden = ruta_pedido(b, "00-00", ["04-04", "00-03", "02-02"], muelles_finales=["04-00"])
    vecinos = {(u, v) for u, v, _ in arcos}
    assert all((u, v) in vecinos for u, v in zip(rec, rec[1:]))  # cada paso es un pasillo
    assert orden == ["00-03", "02-02", "04-04", "04-00"]  # voraz: siempre el más cercano
    assert rec[0] == "00-00" and rec[-1] == "04-00"
    assert len(rec) - 1 == 3 + 3 + 4 + 4  # tramos mínimos en pasillos
    assert b.ops["búsquedas (una por tramo)"] == 4


def test_medir_y_csv(tmp_path):
    r, ms, kb = medir(lambda: [0] * 100_000)
    assert len(r) == 100_000 and ms >= 0 and kb > 700  # 100 000 referencias ≈ 800 KB
    m = Medicion("prueba", "X", "O(1)", ms, kb, {"pasos": 1}, {"valor": 2})
    assert "pasos: 1" in tabla([m])
    guardar_csv([m], tmp_path / "m.csv")
    guardar_csv([m], tmp_path / "m.csv")
    assert len((tmp_path / "m.csv").read_text(encoding="utf-8").splitlines()) == 3  # encabezado + 2


def test_aplicativo_en_el_almacen():
    import app
    a = app.Almacen()
    m, rec = a.ruta("Bellman-Ford", "02-00", ["40-14"], a_despacho=False)
    assert rec[0] == "02-00" and rec[-1] == "40-14"
    assert m.resultado["tiempo del operario"] == "65 s"  # el mismo resultado de la demo de rutas
    flujo, corte = a.flujo()
    assert all(x.resultado["flujo máximo"] == "73 operarios/min" for x in flujo) and len(corte) == 45
    mst, arbol = a.mst()
    assert len(arbol) == 1799


@pytest.mark.parametrize("tipo", ["rutas", "mst", "flujo"])
def test_carrera_graba_eventos_en_orden(tipo):
    import carrera
    from demo import Datos
    d = Datos()
    _, corredores = carrera.preparar(tipo, d, "20-20")
    for c in corredores:
        assert c.eventos and c.tiempos == sorted(c.tiempos)  # el reloj solo avanza
        assert c.tiempos[-1] <= c.total_ms
    if tipo == "rutas":  # BFS descubre cada ubicación una vez (todas menos el origen)
        assert len(corredores[0].eventos) == len(d.nodos) - 1
    if tipo == "mst":  # los dos agregan V - 1 pasillos
        assert all(len(c.eventos) == len(d.nodos) - 1 for c in corredores)
    if tipo == "flujo":  # los dos llegan al flujo máximo
        assert all(sum(cuello for _, (_, cuello) in c.eventos) == 73 for c in corredores)
