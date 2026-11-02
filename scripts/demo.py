"""Demostración de los algoritmos de la Unidad 2 sobre el almacén de KivaFlow.

Cada demo imprime el detalle paso a paso en la consola y guarda una figura del mapa
de 3 zonas en resultados/. Todo está programado a mano en kivaflow/; aquí solo se
cargan los datos, se llama al algoritmo y se dibuja con matplotlib.

Uso:
    python scripts/demo.py mst            # Kruskal y Prim: red de servicio (hoja 10, ej. 2 y 3)
    python scripts/demo.py fuerza-bruta   # MST por fuerza bruta en un sector chico (hoja 10, ej. 1)
    python scripts/demo.py flujo          # Ford-Fulkerson: Recepción -> Despacho y corte mínimo (hoja 11)
    python scripts/demo.py ruta           # Bellman-Ford: ruta de un operario (hoja 13, ej. 1 y 3)
    python scripts/demo.py floyd          # Floyd-Warshall en un sector de Picking (hoja 13, ej. 2)
    python scripts/demo.py mochila        # Mochila 0/1: qué carga el operario en el primer viaje (módulo 12)
    python scripts/demo.py todo           # todas, una tras otra
Agrega --mostrar para abrir cada figura en una ventana.
"""
import argparse
import math
import random
import sys
import time
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
import matplotlib  # noqa: E402

from kivaflow import config, grafo  # noqa: E402
from kivaflow.caminos import bellman_ford, camino, camino_fw, floyd_warshall  # noqa: E402
from kivaflow.flujo import ford_fulkerson, red  # noqa: E402
from kivaflow.mapa import COLOR_NIVEL, fondo, lineas, posiciones, recorrido  # noqa: E402
from kivaflow.mochila import mochila_01  # noqa: E402
from kivaflow.mst import fuerza_bruta, kruskal, prim  # noqa: E402

SALIDA = RAIZ / "resultados"
plt = None  # se importa en main() según --mostrar


def titulo(texto):
    print("\n" + "=" * 78 + f"\n{texto}\n" + "=" * 78)


def guardar(fig, nombre, mostrar):
    SALIDA.mkdir(exist_ok=True)
    ruta = SALIDA / nombre
    fig.savefig(ruta, dpi=105, bbox_inches="tight")
    print(f"\nFigura: {ruta.relative_to(RAIZ)}")
    if mostrar:
        plt.show()
    plt.close(fig)


class Datos:
    def __init__(self):
        self.nodos = grafo.leer_nodos()
        self.filas = grafo.leer_aristas()
        self.pos = posiciones(self.nodos)
        self.nivel = {}
        for a in self.filas:
            self.nivel[(a["Nodo_Origen"], a["Nodo_Destino"])] = a["Frecuencia_Pedidos"]
            self.nivel[(a["Nodo_Destino"], a["Nodo_Origen"])] = a["Frecuencia_Pedidos"]

    def aristas(self, peso="Distancia_Ajustada_m", dentro=None):
        r = [(a["Nodo_Origen"], a["Nodo_Destino"], float(a[peso])) for a in self.filas]
        if dentro is not None:
            r = [x for x in r if x[0] in dentro and x[1] in dentro]
        return r

    def arcos(self, peso="Distancia_Ajustada_m", dentro=None):
        """Los pasillos en los dos sentidos (grafo dirigido para Bellman-Ford y Floyd-Warshall)."""
        a = self.aristas(peso, dentro)
        return a + [(v, u, w) for u, v, w in a]

    def zona(self, prefijo):
        return [k for k, n in self.nodos.items() if n["Zona"].startswith(prefijo)]

    def sector(self, filas, cols):
        return [k for k, n in self.nodos.items() if int(n["Fila"]) in filas and int(n["Columna"]) in cols]


# ----------------------------------------------------------------------------- MST
def demo_mst(d, mostrar):
    import demo_mst as dm
    titulo("MST con Kruskal y Prim: red de servicio de menor congestión (hoja 10, ejercicios 2 y 3)")
    aristas = d.aristas()
    resultados = [dm.medir(kruskal, list(d.nodos), aristas), dm.medir(prim, list(d.nodos), aristas)]
    dm.imprimir_detalle(d.nodos, aristas, d.nivel, resultados)
    dm.ejemplo_a_mano()
    SALIDA.mkdir(exist_ok=True)
    dm.figura_etapas(plt, d.nodos, d.pos, d.nivel, resultados, SALIDA / "mst_etapas.png")
    dm.figura_red(plt, d.nodos, d.pos, d.nivel, resultados[0][0], SALIDA / "mst_red_servicio.png")
    print("Figuras: resultados/mst_etapas.png y resultados/mst_red_servicio.png")
    if mostrar:
        dm.animar(plt, d.nodos, d.pos, d.nivel, resultados)


# --------------------------------------------------------------------- fuerza bruta
def demo_fuerza_bruta(d, mostrar):
    titulo("MST por fuerza bruta en un sector de 3 x 4 (hoja 10, ejercicio 1)")
    sector = d.sector(range(0, 3), range(0, 4))
    aristas = d.aristas(dentro=set(sector))
    V, E = len(sector), len(aristas)
    t0 = time.perf_counter()
    fb = fuerza_bruta(sector, aristas)
    t_fb = (time.perf_counter() - t0) * 1000
    k = kruskal(sector, aristas)
    print(f"Sector: V = {V} ubicaciones, E = {E} pasillos. Un árbol de expansión tiene V - 1 = {V - 1} pasillos.")
    print(f"Subconjuntos de {V - 1} pasillos: C({E}, {V - 1}) = {math.comb(E, V - 1):,}. Se prueban todos.")
    print(f"Fuerza bruta: costo {fb.costo:.2f} en {t_fb:.0f} ms. Kruskal: costo {k.costo:.2f}. Iguales: {abs(fb.costo - k.costo) < 1e-9}")
    total = math.lgamma(3516) - math.lgamma(1800) - math.lgamma(1717)
    print(f"En todo el almacén serían C(3515, 1799) ≈ 10^{total / math.log(10):.0f} subconjuntos: imposible.")
    print("Por eso se usan algoritmos voraces (Kruskal, Prim): llegan al óptimo en O(E log E).")

    fig, axs = plt.subplots(1, 2, figsize=(9, 3.6))
    for ax, r, nombre in ((axs[0], fb, "Fuerza bruta"), (axs[1], k, "Kruskal")):
        xs = [d.pos[n] for n in sector]
        lineas(ax, d.pos, aristas, color="#cccccc", ancho=1)
        lineas(ax, d.pos, r.aristas, color=[COLOR_NIVEL[d.nivel[(u, v)]] for u, v, _ in r.aristas], ancho=3)
        ax.scatter(*zip(*xs), s=40, c="black", zorder=3)
        for u, v, w in aristas:
            (x1, y1), (x2, y2) = d.pos[u], d.pos[v]
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, f"{w:g}", fontsize=7, ha="center", va="center",
                    bbox=dict(facecolor="white", edgecolor="none", pad=0.5))
        ax.set_title(f"{nombre}: costo {r.costo:.2f}", fontsize=10)
        ax.set_aspect("equal")
        ax.axis("off")
    fig.suptitle(f"Sector 3 x 4 de Recepción: fuerza bruta prueba {math.comb(E, V - 1):,} subconjuntos; Kruskal, {k.revisadas} aristas")
    guardar(fig, "fuerza_bruta.png", mostrar)


# ---------------------------------------------------------------------------- flujo
def demo_flujo(d, mostrar):
    titulo("Flujo máximo con Ford-Fulkerson: Recepción -> Despacho (hoja 11, ejercicio 2)")
    cap_nivel = config.CAPACIDAD_OPERARIOS_MIN
    print("Capacidad de cada pasillo (operarios/min, en cada sentido): "
          + ", ".join(f"{n} = {c}" for n, c in cap_nivel.items()))
    print("Fuente: toda la zona de Recepción; sumidero: toda la zona de Despacho (superfuente y supersumidero).")
    cap = red(d.filas, cap_nivel, d.zona("Rec"), d.zona("Emp"))
    t0 = time.perf_counter()
    f = ford_fulkerson(cap)
    ms = (time.perf_counter() - t0) * 1000
    print(f"\n{'Iter.':>5}  {'Cuello':>6}  {'Flujo acumulado':>15}  Camino aumentante (DFS)")
    acumulado = 0
    for i, (c, cuello) in enumerate(f.caminos, 1):
        acumulado += cuello
        if i <= 8 or i == len(f.caminos):
            interior = c[1:-1]
            print(f"{i:>5}  {cuello:>6}  {acumulado:>15}  {interior[0]} -> ... -> {interior[-1]} ({len(interior)} ubicaciones)")
        elif i == 9:
            print(f"{'...':>5}")
    print(f"\nFlujo máximo: {f.valor} operarios/min, con {len(f.caminos)} caminos aumentantes en {ms:.0f} ms.")
    print(f"Veces que un camino usó un arco inverso (cancelar flujo previo): {f.usos_inversos}.")
    cols = Counter((d.nodos[u]["Columna"], d.nodos[v]["Columna"]) for u, v, _ in f.corte)
    print(f"Corte mínimo: {len(f.corte)} pasillos, capacidad total {sum(c for *_, c in f.corte)} "
          f"(= flujo máximo, teorema flujo máximo / corte mínimo).")
    print("Dónde está el corte (columna origen -> columna destino): " + ", ".join(f"{a}->{b}: {n}" for (a, b), n in cols.items()))
    print("Interpretación: esos pasillos de Picking son el cuello de botella; agregar capacidad en otra parte no sube el flujo.")

    fig, ax = plt.subplots(figsize=(9, 10))
    fondo(ax, d.nodos, d.pos, f"Flujo máximo {f.valor} operarios/min · corte mínimo de {len(f.corte)} pasillos", grilla=d.aristas())
    lado = [d.pos[n] for n in f.lado_fuente if n in d.nodos]
    ax.scatter(*zip(*lado), s=3, c="#2b6cb0", zorder=2, label="Lado de la fuente (alcanzable en la red residual)")
    for c, _ in f.caminos[:5]:
        recorrido(ax, d.pos, c[1:-1], color="#38a169", ancho=1.2)
    lineas(ax, d.pos, f.corte, color="#e53e3e", ancho=3.5, z=5)
    ax.plot([], [], color="#e53e3e", linewidth=3.5, label="Pasillos del corte mínimo")
    ax.plot([], [], color="#38a169", linewidth=1.2, label="Primeros 5 caminos aumentantes")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.01), fontsize=9)
    guardar(fig, "flujo_maximo.png", mostrar)


# ----------------------------------------------------------------------------- ruta
def demo_ruta(d, mostrar):
    titulo("Ruta de un operario con Bellman-Ford (hoja 13, ejercicios 1 y 3)")
    origen = "02-00"  # primer muelle de Recepción
    destino = next(k for k, n in d.nodos.items() if n["SKU"] == "SKU0001")  # el producto más pedido
    print(f"Origen: muelle {origen}. Destino: rack {destino} (SKU0001, el producto más pedido).")
    rutas = {}
    for peso, nombre in (("Distancia_m", "solo distancia"), ("Distancia_Ajustada_m", "con congestión")):
        t0 = time.perf_counter()
        b = bellman_ford(list(d.nodos), d.arcos(peso), origen)
        ms = (time.perf_counter() - t0) * 1000
        c = camino(b.padre, destino)
        niveles = Counter(d.nivel[(u, v)] for u, v in zip(c, c[1:]))
        metros = 1.2 * (len(c) - 1)
        ajustado = sum(1.2 * config.FACTOR_CONGESTION[d.nivel[(u, v)]] for u, v in zip(c, c[1:]))
        rutas[nombre] = c
        print(f"\nPeso «{peso}» ({nombre}):")
        print(f"  Rondas de relajación: {b.rondas} de V - 1 = {len(d.nodos) - 1} posibles (se detiene cuando una ronda no mejora nada)")
        print(f"  Relajaciones: {b.relajaciones} · ¿ciclo negativo?: {'sí' if b.ciclo_negativo else 'no'} · {ms:.0f} ms")
        print(f"  Ruta: {len(c) - 1} pasillos = {metros:.1f} m reales, {ajustado:.2f} m ajustados, "
              f"{ajustado / config.VELOCIDAD_M_S:.0f} s a {config.VELOCIDAD_M_S} m/s con congestión")
        print("  Pasillos por congestión: " + ", ".join(f"{n} {niveles[n]}" for n in ("Baja", "Media", "Alta")))

    print("\nCiclo negativo (ejercicio 3): con pesos positivos no puede haber. Prueba con un ciclo de 3 nodos:")
    prueba = bellman_ford(["A", "B", "C"], [("A", "B", 1), ("B", "C", -2), ("C", "A", -1)], "A")
    print(f"  A->B 1, B->C -2, C->A -1 (suma -2): ¿ciclo negativo? {'sí' if prueba.ciclo_negativo else 'no'}")

    fig, ax = plt.subplots(figsize=(9, 10))
    fondo(ax, d.nodos, d.pos, "Bellman-Ford: ruta más corta vs. ruta que evita la congestión", grilla=d.aristas())
    altas = [(u, v) for (u, v), n in d.nivel.items() if n == "Alta" and u < v]
    lineas(ax, d.pos, altas, color="#f6c1c1", ancho=1.2)
    recorrido(ax, d.pos, rutas["solo distancia"], "#718096", etiqueta="Solo distancia (menos pasillos)")
    recorrido(ax, d.pos, rutas["con congestión"], "#2b6cb0", etiqueta="Con congestión (distancia ajustada)")
    ax.plot([], [], color="#f6c1c1", linewidth=1.2, label="Pasillos de congestión alta")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.01), fontsize=9)
    guardar(fig, "ruta_bellman_ford.png", mostrar)


# ---------------------------------------------------------------------------- floyd
def demo_floyd(d, mostrar):
    titulo("Floyd-Warshall en un sector de Picking de 10 x 10 (hoja 13, ejercicio 2)")
    sector = d.sector(range(0, 10), range(13, 23))
    arcos = d.arcos(dentro=set(sector))
    t0 = time.perf_counter()
    nodos, dist, sig = floyd_warshall(sector, arcos)
    ms = (time.perf_counter() - t0) * 1000
    V = len(nodos)
    print(f"V = {V} ubicaciones, {len(arcos)} arcos. Tres bucles anidados: V³ = {V ** 3:,} comparaciones en {ms:.0f} ms.")
    print(f"En todo el almacén serían 1800³ ≈ {1800 ** 3:.1e}: por eso Floyd-Warshall se usa en un sector y")
    print("Bellman-Ford (un origen) en el almacén completo.")
    puntos = ["00-13", "00-22", "05-17", "09-13", "09-22"]
    idx = {n: i for i, n in enumerate(nodos)}
    print("\nMatriz de distancias ajustadas (m) entre 5 ubicaciones del sector:")
    print(" " * 8 + "".join(f"{p:>8}" for p in puntos))
    for a in puntos:
        print(f"{a:>8}" + "".join(f"{dist[idx[a]][idx[b]]:>8.2f}" for b in puntos))
    c = camino_fw(nodos, sig, "00-13", "09-22")
    b = bellman_ford(sector, arcos, "00-13")
    print(f"\nCamino 00-13 -> 09-22 reconstruido con la matriz «siguiente»: {len(c) - 1} pasillos, "
          f"{dist[idx['00-13']][idx['09-22']]:.2f} m ajustados.")
    print(f"Comprobación con Bellman-Ford desde 00-13: {b.dist['09-22']:.2f} m (igual: "
          f"{abs(b.dist['09-22'] - dist[idx['00-13']][idx['09-22']]) < 1e-9}).")

    fig, axs = plt.subplots(1, 2, figsize=(13, 6))
    fondo(axs[0], d.nodos, d.pos, "Sector de 10 x 10 en Picking y un camino de la matriz", grilla=d.aristas())
    ys = [d.pos[n] for n in sector]
    axs[0].scatter(*zip(*ys), s=4, c="#4a5568", zorder=3)
    recorrido(axs[0], d.pos, c, "#805ad5")
    axs[0].set_xlim(13 * 1.2 - 2, 23 * 1.2 + 1)
    axs[0].set_ylim(-11 * 1.2, 1.5)
    im = axs[1].imshow(dist, cmap="viridis")
    axs[1].set_title("Matriz de distancias de Floyd-Warshall (100 x 100)", fontsize=10)
    axs[1].set_xlabel("ubicación destino (índice)")
    axs[1].set_ylabel("ubicación origen (índice)")
    fig.colorbar(im, ax=axs[1], label="m ajustados")
    guardar(fig, "floyd_warshall.png", mostrar)


# -------------------------------------------------------------------------- mochila
def demo_mochila(d, mostrar):
    titulo("Mochila 0/1 con programación dinámica: qué lleva el operario en el primer viaje")
    rng = random.Random(config.SEMILLA)
    racks = [k for k, n in d.nodos.items() if n["Tipo"] == "rack"]
    pedido = sorted(rng.sample(racks, 10))
    pesos = [rng.randint(1, 8) for _ in pedido]
    urgencia = [rng.randint(1, 10) for _ in pedido]
    W = 20
    print(f"Pedido de {len(pedido)} productos; el carrito lleva como máximo W = {W} kg.")
    print("Pesos y urgencias son sintéticos (semilla 2026), como el resto del dataset.\n")
    print(f"{'#':>2}  {'Rack':>6}  {'SKU':>8}  {'Peso kg':>7}  {'Urgencia':>8}")
    for i, (r, p, u) in enumerate(zip(pedido, pesos, urgencia), 1):
        print(f"{i:>2}  {r:>6}  {d.nodos[r]['SKU']:>8}  {p:>7}  {u:>8}")
    valor, elegidos, dp = mochila_01(pesos, urgencia, W)
    print(f"\nTabla dp[i][c] (mejor urgencia con los primeros i productos y capacidad c), columnas c = 0, 5, ..., {W}:")
    cols = list(range(0, W + 1, 5))
    print("   i " + "".join(f"{c:>5}" for c in cols))
    for i, fila in enumerate(dp):
        print(f"{i:>4} " + "".join(f"{fila[c]:>5}" for c in cols))
    print(f"\nRespuesta dp[{len(pedido)}][{W}] = {valor}. Reconstrucción (de la última fila hacia arriba: si "
          "dp[i][c] != dp[i-1][c], el producto i entra):")
    print(f"  Primer viaje: productos {[i + 1 for i in elegidos]}, {sum(pesos[i] for i in elegidos)} kg, urgencia {valor}.")
    resto = [i for i in range(len(pedido)) if i not in elegidos]
    print(f"  Segundo viaje: productos {[i + 1 for i in resto]}, {sum(pesos[i] for i in resto)} kg.")
    print(f"Complejidad: O(n · W) = {len(pedido)} x {W} = {len(pedido) * W} celdas. Por fuerza bruta serían 2^{len(pedido)} = {2 ** len(pedido)} combinaciones.")
    voraz = sorted(range(len(pedido)), key=lambda i: urgencia[i] / pesos[i], reverse=True)
    carga = vz = 0
    for i in voraz:
        if carga + pesos[i] <= W:
            carga += pesos[i]
            vz += urgencia[i]
    print(f"Voraz por urgencia/kg (módulo 12): urgencia {vz}. {'Igual que DP.' if vz == valor else 'Menor que DP: el voraz no garantiza el óptimo en la mochila 0/1.'}")

    fig, ax = plt.subplots(figsize=(9, 10))
    fondo(ax, d.nodos, d.pos, f"Mochila 0/1: primer viaje (urgencia {valor}, {sum(pesos[i] for i in elegidos)} de {W} kg)", grilla=d.aristas())
    for i, r in enumerate(pedido):
        x, y = d.pos[r]
        dentro = i in elegidos
        ax.scatter([x], [y], s=160, c="#38a169" if dentro else "#a0aec0", edgecolors="black", zorder=6)
        ax.annotate(f"{i + 1}: {pesos[i]} kg, u={urgencia[i]}", (x, y), xytext=(6, 6), textcoords="offset points", fontsize=8)
    ax.scatter([], [], s=80, c="#38a169", edgecolors="black", label="Va en el primer viaje")
    ax.scatter([], [], s=80, c="#a0aec0", edgecolors="black", label="Queda para el segundo viaje")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.01), fontsize=9)
    guardar(fig, "mochila.png", mostrar)


DEMOS = {"mst": demo_mst, "fuerza-bruta": demo_fuerza_bruta, "flujo": demo_flujo,
         "ruta": demo_ruta, "floyd": demo_floyd, "mochila": demo_mochila}


def main():
    global plt
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("demo", choices=[*DEMOS, "todo"])
    p.add_argument("--mostrar", action="store_true", help="abrir cada figura en una ventana")
    args = p.parse_args()
    if not args.mostrar:
        matplotlib.use("Agg")
    import matplotlib.pyplot as _plt
    plt = _plt
    d = Datos()
    for nombre, f in DEMOS.items():
        if args.demo in (nombre, "todo"):
            f(d, args.mostrar)


if __name__ == "__main__":
    main()
