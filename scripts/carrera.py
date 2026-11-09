"""Carrera en el tiempo: dos algoritmos resuelven lo mismo y se ve, con un reloj
común, qué hizo cada uno en cada instante.

No es paso a paso: cada algoritmo se ejecuta de verdad y anota el instante exacto
(`time.perf_counter`) de cada avance (una ubicación alcanzada, un pasillo agregado
al árbol, un camino de aumento). Después se reproduce en cámara lenta, con el
mismo reloj para los dos, así que el que termina primero en la animación es el
que de verdad fue más rápido. Abajo, la curva de progreso muestra cómo avanza
cada uno en el tiempo.

Uso:
    python scripts/carrera.py rutas            # BFS vs. Bellman-Ford desde un muelle
    python scripts/carrera.py mst              # Kruskal vs. Prim
    python scripts/carrera.py flujo            # Edmonds-Karp vs. Ford-Fulkerson (DFS)
    python scripts/carrera.py rutas --origen 20-20 --duracion 15
    python scripts/carrera.py mst --guardar    # además guarda resultados/carrera_mst.gif
"""
import argparse
import bisect
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))

from kivaflow import config  # noqa: E402
from kivaflow.caminos import bellman_ford, bfs  # noqa: E402
from kivaflow.flujo import edmonds_karp, ford_fulkerson, red  # noqa: E402
from kivaflow.mst import kruskal, prim  # noqa: E402

FPS = 25
COLOR = {"BFS": "#718096", "Bellman-Ford": "#2b6cb0", "Kruskal + UFDS": "#2f855a", "Prim (heap)": "#38a169",
         "Edmonds-Karp": "#e53e3e", "Ford-Fulkerson (DFS)": "#dd6b20"}


def grabar(funcion, *args, **kwargs):
    """Ejecuta `funcion` y devuelve (resultado, [(t_ms, evento)], total_ms).

    Antes hace una corrida de calentamiento sin grabar, para que la primera
    corrida no pague la carga de cachés y le gane injustamente el otro algoritmo.
    """
    funcion(*args, **kwargs)
    eventos = []
    t0 = time.perf_counter()

    def al_evento(e):
        eventos.append(((time.perf_counter() - t0) * 1000, e))

    r = funcion(*args, al_evento=al_evento, **kwargs)
    return r, eventos, (time.perf_counter() - t0) * 1000


class Corredor:
    """Lo que hace falta para dibujar un algoritmo en la carrera."""

    def __init__(self, nombre, eventos, total_ms, tipo, unidad, a_dibujo):
        self.nombre, self.eventos, self.total_ms = nombre, eventos, total_ms
        self.tiempos = [t for t, _ in eventos]
        self.tipo, self.unidad = tipo, unidad  # tipo: "puntos" o "lineas"
        self.dibujo = [a_dibujo(e) for _, e in eventos]  # lo que se dibuja por evento
        vistos, self.colores = set(), []  # en «puntos»: naranja si el nodo ya había aparecido (se volvió a mejorar)
        for _, e in eventos:
            repetido = isinstance(e, str) and e in vistos
            self.colores.append("#dd6b20" if repetido else COLOR[nombre])
            if isinstance(e, str):
                vistos.add(e)


def preparar(tipo, d, origen):
    """Corre los dos algoritmos de la carrera y devuelve (título, [Corredor, Corredor])."""
    pos = d.pos
    if tipo == "rutas":
        _, e1, t1 = grabar(bfs, list(d.nodos), d.arcos("Distancia_m"), origen)
        _, e2, t2 = grabar(bellman_ford, list(d.nodos), d.arcos("Distancia_Ajustada_m"), origen)
        return (f"Rutas desde {origen}: BFS descubre cada ubicación una vez; Bellman-Ford mejora distancias hasta que ya no cambian\n"
                "(naranja = una distancia que Bellman-Ford volvió a mejorar en una ronda posterior)",
                [Corredor("BFS", e1, t1, "puntos", "ubicaciones descubiertas", lambda v: [pos[v]]),
                 Corredor("Bellman-Ford", e2, t2, "puntos", "mejoras de distancia", lambda v: [pos[v]])])
    if tipo == "mst":
        aristas = d.aristas()
        _, e1, t1 = grabar(kruskal, list(d.nodos), aristas)
        _, e2, t2 = grabar(prim, list(d.nodos), aristas)
        seg = lambda a: [(pos[a[0]], pos[a[1]])]  # noqa: E731
        return ("Red de servicio: Kruskal une bosques en todo el almacén; Prim hace crecer un solo árbol",
                [Corredor("Kruskal + UFDS", e1, t1, "lineas", "pasillos en el árbol", seg),
                 Corredor("Prim (heap)", e2, t2, "lineas", "pasillos en el árbol", seg)])
    if tipo == "flujo":
        cap = red(d.filas, config.CAPACIDAD_OPERARIOS_MIN, d.zona("Rec"), d.zona("Emp"))
        _, e1, t1 = grabar(edmonds_karp, cap)
        _, e2, t2 = grabar(ford_fulkerson, cap)
        seg = lambda e: [(pos[u], pos[v]) for u, v in zip(e[0][1:-2], e[0][2:-1])]  # sin la superfuente ni el supersumidero  # noqa: E731
        return ("Flujo máximo Recepción -> Despacho: cada trazo es un camino de aumento (BFS: los más cortos primero)",
                [Corredor("Edmonds-Karp", e1, t1, "lineas", "caminos de aumento", seg),
                 Corredor("Ford-Fulkerson (DFS)", e2, t2, "lineas", "caminos de aumento", seg)])
    raise ValueError(tipo)


def carrera(plt, d, tipo="rutas", origen="02-00", duracion=12.0):
    """Arma la figura y la animación. Devuelve (fig, anim); hay que guardar `anim`
    en una variable mientras se muestra, o Python la borra."""
    from matplotlib.animation import FuncAnimation
    from matplotlib.collections import LineCollection

    from kivaflow.mapa import fondo

    titulo, corredores = preparar(tipo, d, origen)
    fin_ms = max(c.total_ms for c in corredores)
    cuadros = int(duracion * FPS)
    reloj = [fin_ms * i / (cuadros - 1) for i in range(cuadros)]

    fig = plt.figure(figsize=(14, 9.4))
    fig.canvas.manager.set_window_title(f"KivaFlow · carrera en el tiempo ({tipo})")
    fig.suptitle(titulo, fontsize=10, y=0.99)
    mapas = [fig.add_axes([0.03 + 0.48 * i, 0.31, 0.45, 0.58]) for i in range(2)]
    curva = fig.add_axes([0.07, 0.06, 0.88, 0.19])

    import numpy as np

    estilo_texto = dict(transform=None, ha="center", va="top", fontsize=9, zorder=10,
                        bbox=dict(boxstyle="round", facecolor="white", alpha=0.9, edgecolor="#cbd5e0"))
    dibujos = []  # por corredor: función que actualiza su mapa hasta el evento n
    for ax, c in zip(mapas, corredores):
        fondo(ax, d.nodos, d.pos, titulo=c.nombre, grilla=d.aristas())
        texto = ax.text(0.5, 0.985, "", **(estilo_texto | {"transform": ax.transAxes}))
        if c.tipo == "puntos":
            pts = np.array([dib[0] for dib in c.dibujo]).reshape(-1, 2)
            rep = np.array([col != COLOR[c.nombre] for col in c.colores], dtype=bool)
            (nuevo,) = ax.plot([], [], "o", ms=3.2, color=COLOR[c.nombre], zorder=5, animated=True)
            (otra,) = ax.plot([], [], "o", ms=3.2, color="#dd6b20", zorder=6, animated=True)
            if tipo == "rutas":
                ax.scatter(*d.pos[origen], s=120, c="#d69e2e", edgecolors="black", zorder=7)

            def actualizar(n, pts=pts, rep=rep, nuevo=nuevo, otra=otra):
                sub, r = pts[:n], rep[:n]
                nuevo.set_data(sub[~r, 0], sub[~r, 1])
                otra.set_data(sub[r, 0], sub[r, 1])
                return [nuevo, otra]
        else:
            segs = [s for dib in c.dibujo for s in dib]
            cuantos = np.cumsum([0] + [len(dib) for dib in c.dibujo])
            col = LineCollection([], colors=COLOR[c.nombre], linewidths=1.6 if tipo == "mst" else 1.1,
                                 zorder=5, animated=True)
            ax.add_collection(col)

            def actualizar(n, segs=segs, cuantos=cuantos, col=col):
                col.set_segments(segs[:cuantos[n]])
                return [col]
        texto.set_animated(True)
        dibujos.append((actualizar, texto))

    lineas_tiempo = []
    for c in corredores:
        total = max(len(c.eventos), 1)
        xs = np.array([0] + c.tiempos + [c.total_ms])
        ys = np.array([0] + [100 * (i + 1) / total for i in range(len(c.eventos))] + [100])
        curva.plot(xs, ys, color=COLOR[c.nombre], alpha=0.18, linewidth=2)
        (ln,) = curva.plot([], [], color=COLOR[c.nombre], linewidth=2.2, animated=True,
                           label=f"{c.nombre}: {len(c.eventos):,} {c.unidad} en {c.total_ms:.1f} ms".replace(",", " "))
        lineas_tiempo.append((ln, xs, ys))
    marca = curva.axvline(0, color="black", linewidth=1, animated=True)
    curva.set_xlim(0, fin_ms * 1.02)
    curva.set_ylim(0, 105)
    curva.set_xlabel("tiempo real del algoritmo (ms)")
    curva.set_ylabel("% de su trabajo")
    curva.legend(loc="lower right", fontsize=8)
    curva.grid(alpha=0.3)

    def cuadro(i):
        t = reloj[i]
        cambiados = [marca]
        for c, (actualizar, texto), (ln, xs, ys) in zip(corredores, dibujos, lineas_tiempo):
            n = bisect.bisect_right(c.tiempos, t)
            cambiados += actualizar(n)
            listo = t >= c.total_ms
            texto.set_text(f"{'✔ terminó' if listo else 'trabajando…'} · {n:,} {c.unidad}\n"
                           f"t = {min(t, c.total_ms):.2f} ms de {c.total_ms:.2f} ms".replace(",", " "))
            texto.set_color("#2f855a" if listo else "black")
            k = n + 2 if listo else n + 1  # incluye el 0 inicial y, al terminar, el punto final
            ln.set_data(xs[:k], ys[:k])
            cambiados += [texto, ln]
        marca.set_xdata([t, t])
        return cambiados

    anim = FuncAnimation(fig, cuadro, frames=cuadros, interval=1000 / FPS, repeat=False, blit=True)
    fig.text(0.5, 0.005, f"Cámara lenta: {fin_ms:.1f} ms reales se muestran en {duracion:.0f} s. "
             "Anotar cada evento agrega un poco de tiempo a los dos por igual.", ha="center", fontsize=8,
             color="#4a5568")
    return fig, anim


def main():
    import matplotlib.pyplot as plt

    from demo import Datos

    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("tipo", choices=["rutas", "mst", "flujo"])
    p.add_argument("--origen", default="02-00", help="para «rutas»: ubicación de salida (fila-columna)")
    p.add_argument("--duracion", type=float, default=12, help="segundos que dura la animación")
    p.add_argument("--guardar", action="store_true", help="guardar resultados/carrera_<tipo>.gif")
    args = p.parse_args()
    d = Datos()
    if args.origen not in d.nodos:
        sys.exit(f"No existe la ubicación {args.origen} (formato fila-columna, por ejemplo 02-00).")
    fig, anim = carrera(plt, d, args.tipo, args.origen, args.duracion)
    if args.guardar:
        salida = RAIZ / "resultados" / f"carrera_{args.tipo}.gif"
        salida.parent.mkdir(exist_ok=True)
        anim.save(salida, writer="pillow", fps=FPS, dpi=60)
        print(f"Animación guardada en {salida.relative_to(RAIZ)}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
