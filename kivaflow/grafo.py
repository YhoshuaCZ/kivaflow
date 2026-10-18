"""Carga el dataset (CSV) como lista de adyacencia, la estructura que usarán los algoritmos."""
import csv
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"


def leer_nodos(ruta=DATA / "nodos.csv"):
    with open(ruta, newline="", encoding="utf-8") as f:
        return {fila["Nodo"]: fila for fila in csv.DictReader(f)}


def leer_aristas(ruta=DATA / "aristas.csv"):
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def adyacencia(aristas, peso="Distancia_Ajustada_m"):
    """{nodo: [(vecino, peso), ...]}. Los pasillos se recorren en ambos sentidos."""
    ady = {}
    for a in aristas:
        u, v, w = a["Nodo_Origen"], a["Nodo_Destino"], float(a[peso])
        ady.setdefault(u, []).append((v, w))
        ady.setdefault(v, []).append((u, w))
    return ady
