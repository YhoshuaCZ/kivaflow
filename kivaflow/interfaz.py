"""Aspecto de las ventanas de KivaFlow (matplotlib): colores, tarjetas, botones y la
tabla que compara dos algoritmos lado a lado.

El estilo sigue el de los visualizadores de algoritmos más usados (VisuAlgo,
Pathfinding Visualizer): cabecera oscura, lienzo claro, paneles como tarjetas
blancas, un color por algoritmo y los resultados en una tabla, no en texto suelto.
Aquí no hay nada de algoritmos: solo dibujo.
"""
import textwrap

from matplotlib.patches import FancyBboxPatch, Rectangle

FONDO = "#eef2f7"
TARJETA = "#ffffff"
BORDE = "#d5dde8"
TINTA = "#0f172a"
SUAVE = "#64748b"
CABECERA = "#0f172a"
ACENTO = "#2563eb"
FRANJA = "#f6f8fb"  # filas alternas de la tabla
BOTON = {  # tipo: (fondo, fondo al pasar el mouse, texto, borde)
    "principal": (ACENTO, "#1d4ed8", "#ffffff", ACENTO),
    "normal": ("#ffffff", "#e8eefc", TINTA, BORDE),
    "carrera": ("#fef3c7", "#fde68a", "#78350f", "#f5d889"),
}
COLOR_ALGO = {"BFS": "#64748b", "Bellman-Ford": "#2563eb", "voraz": "#ea580c", "óptimo": "#059669",
              "Edmonds-Karp": "#dc2626", "Ford-Fulkerson (DFS)": "#ea580c",
              "Kruskal + UFDS": "#059669", "Prim (heap)": "#0d9488"}
FUENTES = ["Segoe UI", "Inter", "Helvetica Neue", "Arial", "DejaVu Sans"]


def aplicar_tema(plt):
    plt.rcParams.update({"font.family": "sans-serif", "font.sans-serif": FUENTES, "figure.facecolor": FONDO,
                         "axes.edgecolor": BORDE, "axes.titlecolor": TINTA, "text.color": TINTA,
                         "axes.labelcolor": SUAVE, "xtick.color": SUAVE, "ytick.color": SUAVE,
                         "legend.frameon": False, "toolbar": "toolbar2"})


def cabecera(fig, titulo, subtitulo, derecha=""):
    """Barra oscura arriba con el nombre de la app y los datos del almacén."""
    ax = fig.add_axes([0, 0.945, 1, 0.055])
    ax.set_facecolor(CABECERA)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_visible(False)
    ax.text(0.014, 0.5, titulo, color="white", fontsize=15, fontweight="bold", va="center", transform=ax.transAxes)
    ax.text(0.094, 0.47, subtitulo, color="#94a3b8", fontsize=9.5, va="center", transform=ax.transAxes)
    ax.text(0.988, 0.5, derecha, color="#cbd5e1", fontsize=9, va="center", ha="right", transform=ax.transAxes)
    return ax


def tarjeta(fig, rect, titulo=None):
    """Un panel blanco con borde. Devuelve sus ejes, sin marcas."""
    ax = fig.add_axes(rect)
    ax.set_facecolor(TARJETA)
    ax.set_xticks([])
    ax.set_yticks([])
    for s in ax.spines.values():
        s.set_edgecolor(BORDE)
    if titulo:
        ax.set_title(titulo, fontsize=8.5, loc="left", color=SUAVE, fontweight="bold", pad=4)
    return ax


def estilo_boton(boton, tipo="normal"):
    fondo, encima, texto, borde = BOTON[tipo]
    boton.color, boton.hovercolor = fondo, encima
    boton.ax.set_facecolor(fondo)
    boton.label.set_color(texto)
    boton.label.set_fontsize(9)
    boton.label.set_fontweight("bold" if tipo == "principal" else "normal")
    for s in boton.ax.spines.values():
        s.set_edgecolor(borde)


def _miles(v):
    return f"{v:,}".replace(",", " ") if isinstance(v, int) else str(v)


def filas_de(mediciones, omitir=("orden de visita",)):
    """[(sección o None, etiqueta, [valor por medición])] para la tabla comparativa."""
    filas = [(None, "Complejidad", [m.complejidad for m in mediciones]),
             (None, "Tiempo de cálculo", [f"{m.ms:.1f} ms" for m in mediciones]),
             (None, "Memoria pico", [f"{m.pico_kb:.0f} KB" for m in mediciones])]
    for seccion, campo in (("RESULTADO", "resultado"), ("OPERACIONES", "operaciones")):
        claves = list(dict.fromkeys(k for m in mediciones for k in getattr(m, campo) if k not in omitir))
        for i, k in enumerate(claves):
            filas.append((seccion if i == 0 else None, k[0].upper() + k[1:],
                          [_miles(getattr(m, campo).get(k, "—")) for m in mediciones]))
    return filas


def tabla_comparativa(ax, encabezado, mediciones=(), colores=(), conclusion="", pie=()):
    """Dibuja en `ax` el resumen del pedido, la conclusión y una columna por algoritmo.

    `pie`: [(color, texto)] que va debajo de la tabla (por ejemplo el orden de visita).
    """
    ax.clear()
    ax.set_facecolor(TARJETA)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    y = 0.965
    for linea in encabezado:
        ax.text(0.025, y, linea, fontsize=8.5, color=SUAVE, va="top")
        y -= 0.045
    if conclusion:
        alto = 0.05 + 0.04 * conclusion.count("\n")
        ax.add_patch(FancyBboxPatch((0.025, y - alto - 0.005), 0.95, alto, boxstyle="round,pad=0.004,rounding_size=0.012",
                                    facecolor="#eff6ff", edgecolor="#bfdbfe", linewidth=1))
        ax.text(0.04, y - alto / 2 - 0.005, conclusion, fontsize=9, color="#1e3a8a", va="center", fontweight="bold")
        y -= alto + 0.03
    if not mediciones:
        return
    filas = filas_de(mediciones)
    lineas_pie = [(c if j == 0 else None, t2) for c, t in pie for j, t2 in enumerate(textwrap.wrap(t, 96))]
    paso = min(0.052, (y - 0.03 - 0.036 * len(lineas_pie)) / (len(filas) + 1.6))
    x_etq, x_col = 0.04, [0.47, 0.74] if len(mediciones) > 1 else [0.47]
    y -= paso
    for x, m, color in zip(x_col, mediciones, colores):
        ax.text(x, y + paso * 0.5, m.algoritmo, fontsize=9, color="white", fontweight="bold", va="center",
                bbox=dict(boxstyle="round,pad=0.35", facecolor=color, edgecolor="none"))
    for i, (seccion, etiqueta, valores) in enumerate(filas):
        y -= paso
        if i % 2 == 0:
            ax.add_patch(Rectangle((0.025, y), 0.95, paso, facecolor=FRANJA, edgecolor="none"))
        if seccion:
            ax.plot([0.025, 0.975], [y + paso, y + paso], color=BORDE, linewidth=0.8)
        ax.text(x_etq, y + paso * 0.5, etiqueta, fontsize=8.5, color=TINTA, va="center")
        for x, v in zip(x_col, valores):
            ax.text(x, y + paso * 0.5, v, fontsize=8.5, color=TINTA, va="center",
                    family="monospace" if i == 0 else None)
    y -= 0.03
    for color, texto in lineas_pie:
        if color:
            ax.text(0.04, y, "●", fontsize=8, color=color, va="top")
        ax.text(0.062, y, texto, fontsize=7.8, color=SUAVE, va="top")
        y -= 0.036
