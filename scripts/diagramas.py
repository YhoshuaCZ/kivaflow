"""Diagramas con Graphviz, la herramienta de los cuadernos del curso (10_MST_Algoritmo_Kruskal_LA).

Genera en docs/image/:
    arquitectura.png     las capas del aplicativo y qué módulo usa a cuál (para «Diseño del aplicativo»)
    flujo_pedido.png     qué pasa desde el clic en el mapa hasta la tabla de resultados
    sector_mst.png       un sector de 6 × 6 de Picking dibujado como en el cuaderno del profe,
                         con el MST de Kruskal resaltado en naranja
y en data/:
    sector_picking.in    ese mismo sector como lista de adyacencia ponderada, en el formato
                         «vecino|peso» que lee la función readAdjl del cuaderno (pesos en cm, enteros)

Uso:
    python scripts/diagramas.py

Necesita el paquete `graphviz` de Python (pip install graphviz) y el programa Graphviz
instalado (https://graphviz.org/download/; en Google Colab ya viene). El resto de
KivaFlow no lo necesita.
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

from kivaflow.mst import kruskal  # noqa: E402

SALIDA = RAIZ / "docs" / "image"
FUENTE = "Helvetica"
CAPAS = [  # (capa, color de fondo, [(módulo, qué hace)])
    ("Interfaz", "#dbeafe", [("scripts/app.py", "ventana y consola"), ("scripts/carrera.py", "carrera en el tiempo"),
                             ("kivaflow/interfaz.py · mapa.py", "dibujo")]),
    ("Análisis", "#fef3c7", [("kivaflow/medicion.py", "tiempo, memoria, operaciones"),
                             ("scripts/analisis.py", "escalabilidad"), ("scripts/experimento.py", "160 pedidos")]),
    ("Algoritmos", "#dcfce7", [("caminos.py", "BFS · Bellman-Ford · Floyd-Warshall"),
                               ("flujo.py", "Ford-Fulkerson · Edmonds-Karp"), ("mst.py + ufds.py", "Kruskal · Prim"),
                               ("pedido.py + orden.py", "voraz · Held-Karp"), ("mochila.py", "mochila 0/1")]),
    ("Datos", "#fee2e2", [("scripts/generar_dataset.py", "layout + demanda + tráfico"),
                          ("data/nodos.csv · aristas.csv", "1800 nodos, 3515 aristas"),
                          ("kivaflow/grafo.py", "lista de adyacencia")]),
]


def arquitectura(gv):
    g = gv.Digraph("arquitectura", format="png")
    g.attr(rankdir="TB", fontname=FUENTE, nodesep="0.25", ranksep="0.55", dpi="130", compound="true")
    g.attr("node", shape="box", style="rounded,filled", fillcolor="white", color="#94a3b8", fontname=FUENTE, fontsize="10")
    g.attr("edge", color="#475569", arrowsize="0.7", fontname=FUENTE, fontsize="10")
    primero = []
    for i, (capa, color, modulos) in enumerate(CAPAS):
        with g.subgraph(name=f"cluster_{i}") as c:
            c.attr(label=capa, style="rounded,filled", fillcolor=color, color=color, fontname=f"{FUENTE} bold", fontsize="12")
            for j, (modulo, que) in enumerate(modulos):
                c.node(f"n{i}_{j}", f"<<b>{modulo}</b><br/><font point-size='9' color='#475569'>{que}</font>>")
        primero.append(f"n{i}_{len(modulos) // 2}")
    for i in range(len(CAPAS) - 1):  # cada capa solo usa la de abajo
        g.edge(primero[i], primero[i + 1], ltail=f"cluster_{i}", lhead=f"cluster_{i + 1}", label="  usa")
    return g


def flujo_pedido(gv):
    g = gv.Digraph("flujo", format="png")
    g.attr(rankdir="LR", fontname=FUENTE, dpi="130", nodesep="0.3", ranksep="0.45")
    g.attr("node", shape="box", style="rounded,filled", fillcolor="#f8fafc", color="#94a3b8", fontname=FUENTE, fontsize="10")
    g.attr("edge", color="#475569", arrowsize="0.7", fontname=FUENTE, fontsize="9")
    pasos = [("clic", "Clics en el mapa\n(origen y productos)", "#dbeafe"),
             ("busq", "Una búsqueda por punto\nBFS  O(V + E)\nBellman-Ford  O(V · E)", "#dcfce7"),
             ("orden", "Orden de visita\nvoraz  O(n²)\nHeld-Karp  O(n² · 2ⁿ)", "#dcfce7"),
             ("rec", "Recorrido completo\n(termina en Despacho)", "#f8fafc"),
             ("med", "Medición\ntiempo · memoria · operaciones", "#fef3c7"),
             ("sal", "Mapa + tabla comparativa\ny resultados/mediciones.csv", "#dbeafe")]
    for clave, texto, color in pasos:
        g.node(clave, texto, fillcolor=color)
    for (a, *_), (b, *_) in zip(pasos, pasos[1:]):
        g.edge(a, b)
    g.node("csv", "data/nodos.csv\ndata/aristas.csv", shape="cylinder", fillcolor="#fee2e2")
    g.edge("csv", "busq", label="grafo")
    return g


def sector(d, filas=range(10, 16), cols=range(15, 21)):
    """Nodos del sector, sus aristas [(u, v, peso)] y la lista de adyacencia con índices 0..n-1."""
    nodos = d.sector(filas, cols)
    aristas = d.aristas(dentro=set(nodos))
    idx = {n: i for i, n in enumerate(nodos)}
    la = [[] for _ in nodos]
    for u, v, w in aristas:
        cm = round(w * 100)  # el cuaderno del profe lee pesos enteros
        la[idx[u]].append((idx[v], cm))
        la[idx[v]].append((idx[u], cm))
    return nodos, aristas, la


def guardar_la(nodos, la, ruta):
    """Formato del cuaderno: primera línea con las etiquetas; luego, por nodo, «vecino|peso …»."""
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write(" ".join(nodos) + "\n")
        for vecinos in la:
            f.write(" ".join(f"{v}|{w}" for v, w in vecinos) + "\n")


def sector_mst(gv, d, nodos, aristas):
    """Como adjlShow del cuaderno (nodos «orangered», árbol en naranja), con cada nodo en su lugar del almacén."""
    arbol = {(u, v) for u, v, _ in kruskal(nodos, aristas).aristas}
    g = gv.Graph("sector", format="png", engine="neato")
    g.attr(dpi="130", fontname=FUENTE, label=f"Sector de Picking de 6 × 6: MST de Kruskal en naranja ({len(arbol)} de "
           f"{len(aristas)} pasillos). Pesos = distancia ajustada en cm", labelloc="t", fontsize="11")
    g.attr("node", color="orangered", fontcolor="mediumslateblue", fontname="monospace", fontsize="8",
           shape="circle", width="0.45", fixedsize="true")
    g.attr("edge", fontname="monospace", fontsize="8")
    for n in nodos:
        x, y = d.pos[n]
        g.node(n, pos=f"{x * 0.85},{y * 0.85}!")
    for u, v, w in aristas:
        en_arbol = (u, v) in arbol
        g.edge(u, v, str(round(w * 100)), color="orange" if en_arbol else "gray", penwidth="3" if en_arbol else "1")
    return g


def main():
    try:
        import graphviz as gv
    except ImportError:
        sys.exit("Falta el paquete graphviz: pip install graphviz (y el programa de https://graphviz.org/download/).")
    from demo import Datos
    d = Datos()
    SALIDA.mkdir(parents=True, exist_ok=True)
    nodos, aristas, la = sector(d)
    guardar_la(nodos, la, RAIZ / "data" / "sector_picking.in")
    print("Escrito data/sector_picking.in")
    try:
        for nombre, g in (("arquitectura", arquitectura(gv)), ("flujo_pedido", flujo_pedido(gv)),
                          ("sector_mst", sector_mst(gv, d, nodos, aristas))):
            g.render(str(SALIDA / nombre), cleanup=True)
            print(f"Escrito docs/image/{nombre}.png")
    except gv.ExecutableNotFound:
        sys.exit("El paquete está, pero falta el programa Graphviz (dot): https://graphviz.org/download/")


if __name__ == "__main__":
    main()
