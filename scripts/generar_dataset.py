"""Genera data/nodos.csv, data/aristas.csv y data/skus.csv.

Uso:
    python scripts/generar_dataset.py                                   # pedidos sintéticos (Zipf)
    python scripts/generar_dataset.py --instacart ruta/a/instacart      # pedidos reales de Kaggle

Mismo resultado en cada ejecución (semilla fija en kivaflow/config.py).
"""
import argparse
import csv
import random
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from kivaflow import config, demanda, layout, trafico  # noqa: E402


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--instacart", help="carpeta con order_products__prior.csv de Instacart")
    parser.add_argument("--salida", default=RAIZ / "data", type=Path)
    args = parser.parse_args()

    fuente = "instacart" if args.instacart else "sintetica"
    nodos = layout.construir_nodos()
    aristas = layout.construir_aristas()
    n_racks = sum(n.tipo == "rack" for n in nodos)

    popularidad, pedidos = demanda.cargar(fuente, n_racks, args.instacart)
    rng = random.Random(config.SEMILLA)
    trafico.asignar_skus(nodos, popularidad, rng)
    uso = trafico.simular(nodos, pedidos, rng)
    nivel = trafico.niveles([(a.origen, a.destino) for a in aristas], uso)
    zona = {n.id: n.zona for n in nodos}

    args.salida.mkdir(exist_ok=True)
    with open(args.salida / "nodos.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Nodo", "Fila", "Columna", "X_m", "Y_m", "Zona", "Tipo", "SKU"])
        for n in nodos:
            w.writerow([n.id, n.fila, n.col, n.x_m, n.y_m, n.zona, n.tipo, n.sku])

    with open(args.salida / "aristas.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["Nodo_Origen", "Nodo_Destino", "Pasillo", "Distancia_m", "Cruces_Simulados",
                    "Frecuencia_Pedidos", "Distancia_Ajustada_m", "Tiempo_Estimado_s", "Zona_Origen", "Zona_Destino"])
        for a in aristas:
            freq = nivel[(a.origen, a.destino)]
            ajustada = round(a.distancia_m * config.FACTOR_CONGESTION[freq], 3)
            w.writerow([a.origen, a.destino, a.pasillo, a.distancia_m, uso.get(frozenset((a.origen, a.destino)), 0),
                        freq, ajustada, round(ajustada / config.VELOCIDAD_M_S, 3), zona[a.origen], zona[a.destino]])

    # Solo conteos agregados: los datos crudos de Instacart no se vuelven a publicar.
    with open(args.salida / "skus.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["SKU", "Veces_Pedido", "Fuente"])
        for sku, veces in popularidad:
            w.writerow([sku, veces, fuente])

    niveles = Counter(nivel.values())
    print(f"Fuente de pedidos: {fuente} ({len(pedidos)} pedidos simulados)")
    print(f"Nodos: {len(nodos)} ({n_racks} racks, {len(nodos) - n_racks} estaciones)")
    print(f"Aristas: {len(aristas)} -> Baja {niveles['Baja']}, Media {niveles['Media']}, Alta {niveles['Alta']}")
    print(f"Escrito en {args.salida}")


if __name__ == "__main__":
    main()
