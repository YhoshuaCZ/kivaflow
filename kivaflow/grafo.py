"""Carga el dataset (CSV) en las estructuras que usan los algoritmos."""
import csv
from pathlib import Path

from . import config

DATA = Path(__file__).resolve().parent.parent / "data"


def leer_nodos(ruta=DATA / "nodos.csv"):
    with open(ruta, newline="", encoding="utf-8") as f:
        return {fila["Nodo"]: fila for fila in csv.DictReader(f)}


def leer_aristas(ruta=DATA / "aristas.csv"):
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def leer_popularidad(ruta=DATA / "skus.csv"):
    """{sku: veces_pedido} y la fuente de la demanda ("sintetica" o "instacart")."""
    with open(ruta, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))
    return {r["SKU"]: int(r["Veces_Pedido"]) for r in filas}, (filas[0]["Fuente"] if filas else "")


def peso(arista, perfil="punta"):
    """Distancia ajustada por congestión según la hora (en metros)."""
    return float(arista["Distancia_m"]) * config.PERFILES_HORA[perfil][arista["Frecuencia_Pedidos"]]


def adyacencia(aristas, perfil="punta"):
    """Lista de adyacencia {nodo: [(vecino, peso), ...]}.

    Los pasillos se recorren en ambos sentidos, así que cada arista del CSV
    aparece dos veces. Memoria O(V + E).
    """
    ady = {}
    for a in aristas:
        u, v, w = a["Nodo_Origen"], a["Nodo_Destino"], peso(a, perfil)
        ady.setdefault(u, []).append((v, w))
        ady.setdefault(v, []).append((u, w))
    return ady


def lista_de_aristas(ady):
    """[(u, v, w), ...] dirigidas: la forma que recorre Bellman-Ford en cada ronda."""
    return [(u, v, w) for u, vecinos in ady.items() for v, w in vecinos]


def capacidades(aristas):
    """{u: {v: capacidad}} para el flujo máximo (operarios por minuto, ambos sentidos)."""
    cap = {}
    for a in aristas:
        c = config.CAPACIDAD_OPERARIOS_MIN[a["Frecuencia_Pedidos"]]
        u, v = a["Nodo_Origen"], a["Nodo_Destino"]
        cap.setdefault(u, {})[v] = c
        cap.setdefault(v, {})[u] = c
    return cap
