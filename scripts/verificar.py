"""Compara BFS, Bellman-Ford y Edmonds-Karp con NetworkX y guarda resultados/verificacion.json.

Uso: python scripts/verificar.py   (~1 min)
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from kivaflow import grafo, verificacion  # noqa: E402


def main():
    r = verificacion.verificar(grafo.leer_nodos(), grafo.leer_aristas(), consultas_bfs=500, consultas_bf=250)
    salida = RAIZ / "resultados" / "verificacion.json"
    salida.write_text(json.dumps(r, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    for alg, d in r["algoritmos"].items():
        print(f"{alg:13} {d['aciertos']}/{d['consultas']}  error máx {d['error_max']:.1e}")
    print(f"Escrito {salida} ({r['segundos']} s)")


if __name__ == "__main__":
    main()
