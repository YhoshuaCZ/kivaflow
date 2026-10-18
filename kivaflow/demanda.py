"""De dónde salen los pedidos: sintéticos (Zipf) o reales (Instacart).

Ambas fuentes devuelven lo mismo:
- `popularidad`: lista de (sku, veces_pedido), de más a menos pedido.
- `pedidos`: lista de pedidos, cada uno una lista de SKU.
"""
import csv
import random
from collections import Counter
from pathlib import Path

from . import config


def sinteticos(n_skus, rng):
    skus = [f"SKU{r:04d}" for r in range(1, n_skus + 1)]
    pesos = [1 / r ** config.ZIPF_S for r in range(1, n_skus + 1)]
    pedidos = []
    for _ in range(config.N_PEDIDOS):
        k = rng.randint(1, config.MAX_PRODUCTOS_POR_PEDIDO)
        pedidos.append(sorted(set(rng.choices(skus, weights=pesos, k=k))))
    conteo = Counter(s for p in pedidos for s in p)
    popularidad = [(s, conteo.get(s, 0)) for s in skus]
    return popularidad, pedidos


def instacart(carpeta, n_skus, rng):
    """Pedidos reales de Instacart Market Basket Analysis (Kaggle).

    Lee `order_products__prior.csv` (order_id, product_id, ...), que tiene ~32 millones
    de filas, en dos pasadas y sin cargarlo entero:
    1. cuenta cuántas veces se pidió cada producto y se queda con los `n_skus` más
       pedidos (uno por rack);
    2. recorre los pedidos (el archivo viene agrupado por order_id) y toma una muestra
       uniforme de `config.N_PEDIDOS` con muestreo de reservorio, O(N_PEDIDOS) de memoria.
    """
    ruta = Path(carpeta) / "order_products__prior.csv"
    conteo = Counter()
    with open(ruta, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            conteo[fila["product_id"]] += 1
    top = [pid for pid, _ in conteo.most_common(n_skus)]
    sku_de = {pid: f"IC{pid}" for pid in top}

    muestra, vistos = [], 0

    def cerrar(pedido):
        nonlocal vistos
        if not pedido:
            return
        vistos += 1
        if len(muestra) < config.N_PEDIDOS:
            muestra.append(sorted(pedido))
        else:
            j = rng.randrange(vistos)
            if j < config.N_PEDIDOS:
                muestra[j] = sorted(pedido)

    actual, pedido = None, set()
    with open(ruta, newline="", encoding="utf-8") as f:
        for fila in csv.DictReader(f):
            if fila["order_id"] != actual:
                cerrar(pedido)
                actual, pedido = fila["order_id"], set()
            if fila["product_id"] in sku_de:
                pedido.add(sku_de[fila["product_id"]])
    cerrar(pedido)

    popularidad = [(sku_de[pid], conteo[pid]) for pid in top]
    return popularidad, muestra


def cargar(fuente, n_skus, carpeta_instacart=None):
    rng = random.Random(config.SEMILLA)
    if fuente == "sintetica":
        return sinteticos(n_skus, rng)
    if fuente == "instacart":
        if not carpeta_instacart:
            raise ValueError("falta la carpeta con los CSV de Instacart")
        return instacart(carpeta_instacart, n_skus, rng)
    raise ValueError(f"fuente desconocida: {fuente}")
