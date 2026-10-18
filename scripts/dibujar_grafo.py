"""Dibuja el grafo del almacén: nodos por zona y pasillos por nivel de congestión.

Uso: python scripts/dibujar_grafo.py   -> docs/grafo.png
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from kivaflow import grafo, visual  # noqa: E402


def main():
    fig = visual.almacen(grafo.leer_nodos(), grafo.leer_aristas())
    salida = RAIZ / "docs" / "grafo.png"
    salida.parent.mkdir(exist_ok=True)
    fig.savefig(salida, dpi=110, bbox_inches="tight")
    print(f"Escrito {salida}")


if __name__ == "__main__":
    main()
