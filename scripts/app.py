"""KivaFlow · aplicativo del hito 2: elige un origen y los productos de un pedido sobre
el mapa, ejecuta los algoritmos y compara su tiempo, memoria y operaciones.

Uso:
    python scripts/app.py                                   # ventana interactiva (matplotlib)
    python scripts/app.py --consola                         # lo mismo en la consola, con un pedido de ejemplo
    python scripts/app.py --consola --origen 02-00 --productos 40-14,10-20,30-30

En la ventana:
    1. Elige el modo de clic (Origen / Agregar producto / Quitar producto) y haz clic en el mapa.
       «Pedido al azar» llena el pedido con productos según su popularidad.
    2. «Ruta del pedido» calcula el recorrido con el algoritmo elegido.
       «Comparar BFS y B-F» corre los dos sobre el mismo pedido y los dibuja juntos.
       «Orden: voraz vs óptimo» compara el orden de visita voraz con el óptimo
       (programación dinámica de Held-Karp) sobre el mismo pedido.
       «Ver congestión» pinta cada pasillo según su nivel (Baja / Media / Alta).
    3. «Flujo máximo» y «Red de servicio (MST)» analizan el almacén completo.
    4. Los botones amarillos «Carrera…» abren una animación en el tiempo real de dos
       algoritmos (ver scripts/carrera.py).
Cada ejecución se agrega a resultados/mediciones.csv.
"""
import argparse
import math
import random
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

from kivaflow import config  # noqa: E402
from kivaflow.flujo import edmonds_karp, ford_fulkerson, red  # noqa: E402
from kivaflow.medicion import Medicion, guardar_csv, medir, tabla  # noqa: E402
from kivaflow.mst import kruskal, prim  # noqa: E402
from kivaflow.orden import MAX_PRODUCTOS, ruta_optima  # noqa: E402
from kivaflow.pedido import Buscador, ruta_pedido  # noqa: E402

CSV = RAIZ / "resultados" / "mediciones.csv"
COMPLEJIDAD_ORDEN = {"voraz": "O(n²)", "óptimo": "O(n² · 2ⁿ)"}
COMPLEJIDAD = {"BFS": "O(V + E)", "Bellman-Ford": "O(V · E)", "Edmonds-Karp": "O(V · E²)",
               "Ford-Fulkerson (DFS)": "O(E · f*)", "Kruskal + UFDS": "O(E log E)", "Prim (heap)": "O(E log V)"}


class Almacen:
    """Los datos y las corridas de cada algoritmo, sin nada de interfaz (sirve igual en consola)."""

    def __init__(self):
        from demo import Datos
        self.d = Datos()
        self.arcos = {"BFS": self.d.arcos("Distancia_m"), "Bellman-Ford": self.d.arcos("Distancia_Ajustada_m")}
        self.muelles_despacho = sorted(k for k, n in self.d.nodos.items()
                                       if n["Tipo"] == "estacion" and n["Zona"].startswith("Emp"))
        self.racks = [k for k, n in self.d.nodos.items() if n["Tipo"] == "rack" and n["SKU"]]
        self.V, self.E = len(self.d.nodos), len(self.d.filas)

    def describir(self, recorrido):
        tramos = list(zip(recorrido, recorrido[1:]))
        niveles = Counter(self.d.nivel[t] for t in tramos)
        ajustado = sum(config.CELDA_M * config.FACTOR_CONGESTION[self.d.nivel[t]] for t in tramos)
        return {"pasillos recorridos": len(tramos),
                "metros reales": f"{config.CELDA_M * len(tramos):.1f} m",
                "metros ajustados": f"{ajustado:.2f} m",
                "tiempo del operario": f"{ajustado / config.VELOCIDAD_M_S:.0f} s",
                "pasillos Alta / Media / Baja": f"{niveles['Alta']} / {niveles['Media']} / {niveles['Baja']}"}

    def ruta(self, algoritmo, origen, productos, a_despacho=True, orden="voraz", repeticiones=3):
        """`orden`: «voraz» (al pendiente más cercano) u «óptimo» (Held-Karp, hasta MAX_PRODUCTOS)."""
        armar = ruta_optima if orden == "óptimo" else ruta_pedido

        def correr():
            b = Buscador(self.d.nodos, self.arcos[algoritmo], algoritmo)
            return b, armar(b, origen, productos, self.muelles_despacho if a_despacho else ())
        (b, (recorrido, visita)), ms, kb = medir(correr, repeticiones=repeticiones)
        ops = dict(b.ops)  # el Buscador es nuevo en cada corrida: cuenta solo una
        res = self.describir(recorrido) | {"orden de visita": " -> ".join([origen] + visita)}
        nombre, comp = algoritmo, COMPLEJIDAD[algoritmo]
        if orden == "óptimo":
            nombre, comp = f"{algoritmo} · óptimo", COMPLEJIDAD_ORDEN["óptimo"]
        return Medicion("ruta del pedido", nombre, comp, ms, kb, ops, res), recorrido

    def comparar_orden(self, origen, productos, a_despacho=True):
        """El mismo pedido con Bellman-Ford y los dos órdenes de visita: [(orden, Medicion, recorrido)]."""
        salida = []
        for orden in ("voraz", "óptimo"):
            m, rec = self.ruta("Bellman-Ford", origen, productos, a_despacho, orden)
            m.algoritmo, m.complejidad = f"Orden {orden}", COMPLEJIDAD_ORDEN[orden]
            salida.append((orden, m, rec))
        return salida

    def flujo(self):
        cap = red(self.d.filas, config.CAPACIDAD_OPERARIOS_MIN, self.d.zona("Rec"), self.d.zona("Emp"))
        salida, corte = [], None
        for nombre, f in (("Edmonds-Karp", edmonds_karp), ("Ford-Fulkerson (DFS)", ford_fulkerson)):
            r, ms, kb = medir(f, cap)
            largo = sum(len(c) - 3 for c, _ in r.caminos) / len(r.caminos)
            ops = {"caminos de aumento": len(r.caminos), "arcos inversos usados": r.usos_inversos}
            res = {"flujo máximo": f"{r.valor} operarios/min", "largo medio del camino": f"{largo:.1f} pasillos",
                   "pasillos del corte mínimo": len(r.corte)}
            salida.append(Medicion("flujo máximo", nombre, COMPLEJIDAD[nombre], ms, kb, ops, res))
            corte = corte or r.corte
        return salida, corte

    def mst(self):
        aristas = self.d.aristas()
        salida, arbol = [], None
        for nombre, f in (("Kruskal + UFDS", kruskal), ("Prim (heap)", prim)):
            r, ms, kb = medir(f, list(self.d.nodos), aristas)
            altas = sum(1 for u, v, _ in r.aristas if self.d.nivel[(u, v)] == "Alta")
            ops = {"aristas revisadas": r.revisadas, "descartadas (ciclo o entrada vieja)": r.descartadas}
            res = {"pasillos del árbol": len(r.aristas), "costo total": f"{r.costo:.2f} m ajustados",
                   "pasillos de congestión Alta": altas}
            salida.append(Medicion("red de servicio", nombre, COMPLEJIDAD[nombre], ms, kb, ops, res))
            arbol = arbol or r.aristas
        return salida, arbol

    def pedido_al_azar(self, n=5, semilla=None):
        rng = random.Random(semilla)
        pesos = [1 / int(self.d.nodos[r]["SKU"][3:]) for r in self.racks]  # Zipf: el SKU0001 es el más pedido
        elegidos = set()
        while len(elegidos) < n:
            elegidos.add(rng.choices(self.racks, weights=pesos)[0])
        return sorted(elegidos)


def encabezado(a):
    return f"Almacén: V = {a.V} ubicaciones, E = {a.E} pasillos"


# ------------------------------------------------------------------------- consola
def consola(args):
    a = Almacen()
    productos = args.productos.split(",") if args.productos else a.pedido_al_azar(5, semilla=2026)
    for p in [args.origen] + productos:
        if p not in a.d.nodos:
            sys.exit(f"No existe la ubicación {p} (formato fila-columna, por ejemplo 02-00).")
    print(encabezado(a))
    print(f"Pedido: origen {args.origen}, productos {', '.join(productos)}, termina en un muelle de Despacho\n")
    rutas = [a.ruta(alg, args.origen, productos)[0] for alg in ("BFS", "Bellman-Ford")]
    orden = [m for _, m, _ in a.comparar_orden(args.origen, productos)] if len(productos) <= MAX_PRODUCTOS else []
    flujo, _ = a.flujo()
    mst, _ = a.mst()
    for nombre, grupo in (("RUTA DEL PEDIDO", rutas), ("ORDEN DE VISITA (con Bellman-Ford)", orden),
                          ("FLUJO MÁXIMO (Recepción -> Despacho)", flujo), ("RED DE SERVICIO (MST)", mst)):
        if grupo:
            print(f"== {nombre} ==\n{tabla(grupo)}\n")
    guardar_csv(rutas + orden + flujo + mst, CSV, extra=f"origen={args.origen}; productos={'|'.join(productos)}")
    print(f"Mediciones agregadas a {CSV.relative_to(RAIZ)}")


# -------------------------------------------------------------------------- ventana
def ventana(prueba=False):
    import matplotlib.pyplot as plt
    from matplotlib.widgets import Button, CheckButtons, RadioButtons

    from kivaflow import interfaz as ui
    from kivaflow.mapa import COLOR_NIVEL, fondo, lineas, recorrido

    ui.aplicar_tema(plt)
    a = Almacen()
    estado = {"origen": "02-00", "productos": a.pedido_al_azar(4, semilla=7)}

    fig = plt.figure(figsize=(15, 9.2))
    fig.canvas.manager.set_window_title("KivaFlow · hito 2")
    ui.cabecera(fig, "KivaFlow", "Rutas de picking y cuellos de botella en un almacén tipo Amazon",
                f"{a.V} ubicaciones · {a.E} pasillos · 3 zonas")
    ax = ui.tarjeta(fig, [0.012, 0.055, 0.465, 0.85])
    ax_res = ui.tarjeta(fig, [0.492, 0.03, 0.496, 0.5])

    estilo_radio = dict(label_props={"fontsize": [9], "color": [ui.TINTA]},
                        radio_props={"s": [38], "edgecolor": [ui.SUAVE]}, activecolor=ui.ACENTO)
    modo = RadioButtons(ui.tarjeta(fig, [0.492, 0.795, 0.155, 0.118], "1 · EL CLIC EN EL MAPA PONE"),
                        ["Origen", "Agregar producto", "Quitar producto"], **estilo_radio)
    algo = RadioButtons(ui.tarjeta(fig, [0.492, 0.672, 0.155, 0.088], "2 · ALGORITMO DE RUTA"),
                        ["Bellman-Ford", "BFS"], **estilo_radio)
    opciones = CheckButtons(ui.tarjeta(fig, [0.492, 0.558, 0.155, 0.08], "3 · OPCIONES"),
                            ["Terminar en Despacho", "Ver congestión"], [True, False],
                            label_props={"fontsize": [9], "color": [ui.TINTA]},
                            frame_props={"s": [38], "edgecolor": [ui.SUAVE]}, check_props={"facecolor": [ui.ACENTO]})

    fig.text(0.662, 0.922, "ACCIONES", fontsize=8.5, color=ui.SUAVE, fontweight="bold")
    botones = {}
    for i, (texto, tipo) in enumerate([
            ("Ruta del pedido", "principal"), ("Comparar BFS y B-F", "principal"),
            ("Orden: voraz vs óptimo", "principal"), ("Pedido al azar", "normal"),
            ("Flujo máximo", "normal"), ("Red de servicio (MST)", "normal"),
            ("Limpiar pedido", "normal"), ("Carrera: BFS vs B-F", "carrera"),
            ("Carrera: Kruskal vs Prim", "carrera"), ("Carrera: flujo", "carrera")]):
        botones[texto] = Button(fig.add_axes([0.662 + (i % 2) * 0.166, 0.863 - (i // 2) * 0.058, 0.158, 0.047]), texto)
        ui.estilo_boton(botones[texto], tipo)
    fig.text(0.662, 0.612, "Carreras (amarillo): dos algoritmos corren de verdad y se reproducen en\n"
             "cámara lenta con el mismo reloj, desde el origen elegido.\n"
             "Tiempo: mejor de 3 corridas · Memoria: pico con tracemalloc ·\n"
             "cada ejecución se guarda en resultados/mediciones.csv.", fontsize=7.6, va="top", color=ui.SUAVE,
             linespacing=1.45)

    def pedido_txt():
        return [f"Origen {estado['origen']}  ·  {len(estado['productos'])} productos: "
                f"{', '.join(estado['productos']) or '—'}"]

    def resultados(mediciones=(), colores=(), conclusion="", pie=(), encabezado=None):
        ui.tabla_comparativa(ax_res, encabezado or pedido_txt(), mediciones, colores, conclusion, pie)

    def leyenda():
        ax.legend(loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=5, fontsize=8, handlelength=1.6,
                  columnspacing=1.2)

    def dibujar_base(titulo):
        ax.clear()
        fondo(ax, a.d.nodos, a.d.pos, None, grilla=a.d.aristas())
        ax.set_ylim(-config.FILAS * config.CELDA_M, 2.6 * config.CELDA_M)
        ax.set_title(titulo, fontsize=10.5, fontweight="bold", loc="left", pad=6)
        for (zona, cols), tono in zip(config.ZONAS, ("#1e40af", "#9f1239", "#166534")):  # nombre de cada zona
            ax.text((cols.start + cols.stop - 1) / 2 * config.CELDA_M, 1.25 * config.CELDA_M, zona.upper(),
                    fontsize=7, color=tono, ha="center", va="center", fontweight="bold")
        if opciones.get_status()[1]:  # cada pasillo con el color de su congestión
            for nivel in ("Media", "Alta"):
                lineas(ax, a.d.pos, [p for p in a.d.aristas() if a.d.nivel[p[:2]] == nivel],
                       color=COLOR_NIVEL[nivel], ancho=0.9, z=2)
                ax.plot([], [], color=COLOR_NIVEL[nivel], linewidth=1.5, label=f"Congestión {nivel.lower()}")
        o = a.d.pos[estado["origen"]]
        ax.scatter([o[0]], [o[1]], s=150, c="#f59e0b", marker="o", edgecolors=ui.TINTA, linewidths=1.2, zorder=8,
                   label="Origen")
        if estado["productos"]:
            xs, ys = zip(*(a.d.pos[p] for p in estado["productos"]))
            ax.scatter(xs, ys, s=110, c="#ef4444", marker="D", edgecolors=ui.TINTA, linewidths=1.2, zorder=8,
                       label="Productos")
            for p in estado["productos"]:
                ax.annotate(f"{p} · {a.d.nodos[p]['SKU']}", a.d.pos[p], xytext=(7, 6), textcoords="offset points",
                            fontsize=7, zorder=9, color=ui.TINTA,
                            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor=ui.BORDE, alpha=0.9))

    def refrescar(titulo="Arma el pedido con clics en el mapa", conclusion="Elige una acción a la derecha."):
        dibujar_base(titulo)
        leyenda()
        resultados(conclusion=conclusion)
        fig.canvas.draw_idle()

    def aviso(texto):
        resultados(conclusion=texto)
        fig.canvas.draw()

    def registrar(mediciones):
        guardar_csv(mediciones, CSV, extra=f"origen={estado['origen']}; productos={'|'.join(estado['productos'])}")
        print(tabla(mediciones) + "\n")

    def metros(m):
        return float(m.resultado["metros ajustados"][:-2])

    def segundos(m):
        return round(metros(m) / config.VELOCIDAD_M_S)

    def visita(m):
        return m.resultado["orden de visita"].replace("->", "→")

    def en_ruta(algoritmos):
        if not estado["productos"]:
            return aviso("Agrega al menos un producto (modo «Agregar producto» y clic en el mapa).")
        mediciones = []
        dibujar_base(f"Ruta del pedido con {' y '.join(algoritmos)}")
        for i, alg in enumerate(algoritmos):
            m, rec = a.ruta(alg, estado["origen"], estado["productos"], opciones.get_status()[0])
            mediciones.append(m)
            recorrido(ax, a.d.pos, rec, ui.COLOR_ALGO[alg], ancho=3.6 - i * 1.6,
                      etiqueta=f"{alg}: {m.resultado['tiempo del operario']}")
        leyenda()
        conclusion = f"El operario tarda {mediciones[0].resultado['tiempo del operario']} con {algoritmos[0]}."
        if len(mediciones) == 2:
            b, f = mediciones
            ahorro = segundos(b) - segundos(f)
            conclusion = (f"Bellman-Ford ahorra {ahorro:.0f} s de caminata ({100 * ahorro / segundos(b):.0f} %) esquivando "
                          f"la congestión,\npero tarda {f.ms / max(b.ms, 0.01):.0f} veces más en calcular la ruta."
                          if ahorro >= 0.5 else "Las dos rutas cuestan lo mismo: el camino corto no estaba congestionado.")
        resultados(mediciones, [ui.COLOR_ALGO[x] for x in algoritmos], conclusion,
                   [(ui.COLOR_ALGO[x], f"Orden de visita (voraz): {visita(m)}") for x, m in zip(algoritmos, mediciones)][:1])
        registrar(mediciones)
        fig.canvas.draw_idle()

    def en_orden(_):
        n = len(estado["productos"])
        if not 2 <= n <= MAX_PRODUCTOS:
            return aviso(f"El orden se compara con 2 a {MAX_PRODUCTOS} productos: el óptimo crece como n² · 2ⁿ.")
        aviso("Calculando el orden óptimo…")
        corridas = a.comparar_orden(estado["origen"], estado["productos"], opciones.get_status()[0])
        dibujar_base("Orden de visita: voraz frente a óptimo (Held-Karp), con Bellman-Ford")
        for i, (orden, m, rec) in enumerate(corridas):
            recorrido(ax, a.d.pos, rec, ui.COLOR_ALGO[orden], ancho=3.6 - i * 1.6,
                      etiqueta=f"{orden.capitalize()}: {m.resultado['tiempo del operario']}")
        leyenda()
        (_, v, _), (_, o, _) = corridas
        ahorro = segundos(v) - segundos(o)
        ordenes = f"{math.factorial(n):,}".replace(",", " ")
        conclusion = (f"El orden óptimo ahorra {ahorro:.0f} s de caminata ({100 * ahorro / segundos(v):.0f} %) frente al voraz."
                      if ahorro >= 0.5 else "En este pedido el voraz ya encontró el orden óptimo.")
        conclusion += f"\nPor fuerza bruta habría que probar {n}! = {ordenes} órdenes."
        resultados([v, o], [ui.COLOR_ALGO["voraz"], ui.COLOR_ALGO["óptimo"]], conclusion,
                   [(ui.COLOR_ALGO["voraz"], f"Voraz: {visita(v)}"), (ui.COLOR_ALGO["óptimo"], f"Óptimo: {visita(o)}")])
        registrar([v, o])
        fig.canvas.draw_idle()

    def en_flujo(_):
        aviso("Calculando el flujo máximo…")
        mediciones, corte = a.flujo()
        dibujar_base(f"Flujo máximo de Recepción a Despacho: corte mínimo de {len(corte)} pasillos")
        lineas(ax, a.d.pos, corte, color="#dc2626", ancho=3.5, z=6)
        ax.plot([], [], color="#dc2626", linewidth=3.5, label="Corte mínimo (cuello de botella)")
        leyenda()
        ek, ff = mediciones
        resultados(mediciones, [ui.COLOR_ALGO[m.algoritmo] for m in mediciones],
                   f"Pasan como máximo {ek.resultado['flujo máximo']}. Edmonds-Karp llega con "
                   f"{ek.operaciones['caminos de aumento']} caminos de aumento;\nFord-Fulkerson con DFS necesita "
                   f"{ff.operaciones['caminos de aumento']}, más largos.",
                   encabezado=["Capacidad por pasillo según su congestión: Baja 3, Media 2, Alta 1 operarios/min"])
        registrar(mediciones)
        fig.canvas.draw_idle()

    def en_mst(_):
        aviso("Calculando la red de servicio…")
        mediciones, arbol = a.mst()
        dibujar_base("Red de servicio: árbol de expansión mínima sobre la distancia ajustada")
        lineas(ax, a.d.pos, arbol, color="#059669", ancho=1.4, z=5)
        ax.plot([], [], color="#059669", linewidth=1.4, label="Pasillos de la red de servicio")
        leyenda()
        k = mediciones[0]
        resultados(mediciones, [ui.COLOR_ALGO[m.algoritmo] for m in mediciones],
                   f"Kruskal y Prim llegan al mismo costo: {k.resultado['costo total']} con "
                   f"{k.resultado['pasillos del árbol']} pasillos,\nsolo {k.resultado['pasillos de congestión Alta']} "
                   "de congestión alta.",
                   encabezado=["El árbol conecta las 1800 ubicaciones con la menor congestión acumulada"])
        registrar(mediciones)
        fig.canvas.draw_idle()

    def en_azar(_):
        estado["productos"] = a.pedido_al_azar(random.randint(3, 6))
        refrescar()

    def en_limpiar(_):
        estado["productos"] = []
        refrescar()

    def en_clic(ev):
        if ev.inaxes is not ax or ev.xdata is None or getattr(fig.canvas.toolbar, "mode", ""):
            return
        fila = min(max(round(-ev.ydata / config.CELDA_M), 0), config.FILAS - 1)
        col = min(max(round(ev.xdata / config.CELDA_M), 0), config.COLUMNAS - 1)
        nodo = f"{fila:02d}-{col:02d}"
        if modo.value_selected == "Origen":
            estado["origen"] = nodo
        elif modo.value_selected == "Agregar producto" and nodo not in estado["productos"]:
            estado["productos"].append(nodo)
        elif modo.value_selected == "Quitar producto" and estado["productos"]:
            cerca = min(estado["productos"], key=lambda p: (a.d.pos[p][0] - ev.xdata) ** 2 + (a.d.pos[p][1] - ev.ydata) ** 2)
            estado["productos"].remove(cerca)
        refrescar()

    def en_carrera(tipo):
        import carrera
        aviso(f"Preparando la carrera ({tipo})… se abre en otra ventana.")
        fig2, estado["anim"] = carrera.carrera(plt, a.d, tipo, estado["origen"])
        fig2.show()
        resultados(conclusion=f"Carrera ({tipo}) abierta en otra ventana. En la de rutas, cambia el origen con un clic\n"
                   "y repite: desde el centro, Bellman-Ford necesita muchas más rondas que desde una esquina.")
        fig.canvas.draw_idle()

    botones["Carrera: BFS vs B-F"].on_clicked(lambda _: en_carrera("rutas"))
    botones["Carrera: Kruskal vs Prim"].on_clicked(lambda _: en_carrera("mst"))
    botones["Carrera: flujo"].on_clicked(lambda _: en_carrera("flujo"))
    botones["Ruta del pedido"].on_clicked(lambda _: en_ruta([algo.value_selected]))
    botones["Comparar BFS y B-F"].on_clicked(lambda _: en_ruta(["BFS", "Bellman-Ford"]))
    botones["Orden: voraz vs óptimo"].on_clicked(en_orden)
    opciones.on_clicked(lambda _: refrescar())
    botones["Flujo máximo"].on_clicked(en_flujo)
    botones["Red de servicio (MST)"].on_clicked(en_mst)
    botones["Pedido al azar"].on_clicked(en_azar)
    botones["Limpiar pedido"].on_clicked(en_limpiar)
    fig.canvas.mpl_connect("button_press_event", en_clic)
    refrescar()
    if prueba:  # para los tests: devuelve la figura y las acciones sin abrir la ventana
        return fig, botones, modo, opciones
    plt.show()


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--consola", action="store_true", help="sin ventana: corre todo e imprime las mediciones")
    p.add_argument("--origen", default="02-00", help="ubicación de salida (fila-columna), por defecto 02-00")
    p.add_argument("--productos", help="ubicaciones separadas por comas; si no se dan, se elige un pedido al azar")
    args = p.parse_args()
    consola(args) if args.consola else ventana()


if __name__ == "__main__":
    main()
