"""KivaFlow · interfaz gráfica (Streamlit).

Tres formas de abrirla:
- En el navegador, sin instalar nada: https://yhoshuacz.github.io/kivaflow/ (corre con stlite).
- Como un .py normal:          python app.py
- Con Streamlit directamente:  streamlit run app.py
"""
import subprocess
import sys

if __name__ == "__main__":
    from streamlit import runtime

    if not runtime.exists():  # se ejecutó con "python app.py": relanzar con Streamlit
        sys.exit(subprocess.call([sys.executable, "-m", "streamlit", "run", __file__]))

import json  # noqa: E402
import random  # noqa: E402
import time  # noqa: E402
import tracemalloc  # noqa: E402
from collections import Counter  # noqa: E402
from pathlib import Path  # noqa: E402

import streamlit as st  # noqa: E402

from kivaflow import config, edmonds_karp as ek, grafo, interactivo, paleta, pedido, simulacion, verificacion  # noqa: E402

RAIZ = Path(__file__).resolve().parent
REPO = "https://github.com/YhoshuaCZ/kivaflow"
ZONAS = [z for z, _ in config.ZONAS]
NOMBRE = interactivo.NOMBRE
COMPLEJIDAD = {"bfs": ("O(V + E)", "O(V)"), "bellman_ford": ("O(V · E)", "O(V)"),
               "edmonds_karp": ("O(V · E²)", "O(V + E)")}
EN_NAVEGADOR = sys.platform == "emscripten"

st.set_page_config(page_title="KivaFlow", page_icon=":material/route:", layout="wide")
ss = st.session_state

# ---------- estilo «Centro de control» ----------
# Inspirado en los visualizadores de algoritmos (VisuAlgo, Algorithm Visualizer, Pathfinding Visualizer)
# y en los tableros de control de almacenes: barra de navegación arriba, panel de control a la izquierda,
# lienzo grande con leyenda, pseudocódigo en una caja oscura y métricas en tarjetas con acento de color.
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;600&display=swap');
html, body, p, li, label, input, textarea, button p, .stMarkdown {{ font-family: {paleta.SANS}; }}
.stApp {{ background: {paleta.PAPEL}; }}
section[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {{ display: none; }}
header[data-testid="stHeader"] {{ background: {paleta.TARJETA}; border-bottom: 1px solid {paleta.BORDE}; }}
.block-container {{ padding-top: 4.6rem; max-width: 1400px; }}
h1, h2, h3 {{ font-family: {paleta.SANS} !important; font-weight: 600 !important; letter-spacing: -0.02em; }}
h1 {{ font-size: 1.9rem !important; padding-bottom: 0 !important; }}
h3 {{ font-size: 1.05rem !important; }}
code, .kf-mono {{ font-family: {paleta.MONO}; }}

/* encabezado de página */
.kf-ruta {{ font-family: {paleta.MONO}; font-size: 12px; color: {paleta.SUAVE}; letter-spacing: .04em; }}
.kf-ruta b {{ color: {paleta.ACENTO}; font-weight: 600; }}
.kf-sub {{ color: {paleta.SUAVE}; margin: 2px 0 6px; max-width: 820px; }}
.kf-estado {{ display: inline-flex; align-items: center; gap: 8px; padding: 6px 12px; border-radius: 999px;
              border: 1px solid {paleta.BORDE}; background: {paleta.TARJETA}; font-size: 12px; color: {paleta.SUAVE};
              float: right; margin-top: 6px; }}
.kf-punto {{ width: 8px; height: 8px; border-radius: 50%; background: {paleta.EXITO};
             box-shadow: 0 0 0 3px {paleta.EXITO}33; }}

/* paneles: st.container(border=True, key="panel-…") */
[class*="st-key-panel"] {{ background: {paleta.TARJETA}; border-color: {paleta.BORDE} !important; border-radius: 12px; }}
.kf-titulo-panel {{ font-size: 11px; font-weight: 600; letter-spacing: .1em; text-transform: uppercase;
                    color: {paleta.SUAVE}; margin-bottom: 2px; }}
.kf-seccion {{ display: flex; align-items: baseline; gap: 12px; margin: 26px 0 10px;
               border-bottom: 1px solid {paleta.BORDE}; padding-bottom: 8px; }}
.kf-seccion b {{ font-size: 1.05rem; }}
.kf-seccion span {{ color: {paleta.SUAVE}; font-size: 13px; }}

/* tarjetas de métricas con barra de acento */
.kf-card {{ background: {paleta.TARJETA}; border: 1px solid {paleta.BORDE}; border-radius: 12px; padding: 14px 16px;
           height: 100%; position: relative; overflow: hidden; }}
.kf-card.acento::before {{ content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px;
                          background: var(--acento, {paleta.ACENTO}); }}
.kf-etq {{ font-size: 11px; font-weight: 600; letter-spacing: .08em; text-transform: uppercase; color: {paleta.SUAVE}; }}
.kf-num {{ font-size: 1.9rem; font-weight: 600; line-height: 1.15; margin: 6px 0 2px;
           font-variant-numeric: tabular-nums; letter-spacing: -0.02em; }}
.kf-num small {{ font-size: .95rem; color: {paleta.SUAVE}; font-weight: 400; }}
.kf-nota {{ font-size: 13px; color: {paleta.SUAVE}; }}
.kf-conclusion {{ background: {paleta.ACENTO}14; border: 1px solid {paleta.ACENTO}55; border-left: 3px solid
                  {paleta.ACENTO}; border-radius: 8px; padding: 12px 16px; font-size: 14px; margin-top: 8px; }}

/* barras comparativas */
.kf-barra {{ display: grid; grid-template-columns: 110px 1fr 90px; align-items: center; gap: 10px;
             font-size: 13px; margin: 6px 0; }}
.kf-barra .pista {{ background: {paleta.REJILLA}; border-radius: 4px; height: 8px; }}
.kf-barra .lleno {{ height: 8px; border-radius: 4px; }}
.kf-barra .valor {{ text-align: right; font-family: {paleta.MONO}; font-size: 12px; }}

/* etiquetas y leyenda tipo Pathfinding Visualizer */
.kf-chip {{ display: inline-block; padding: 2px 9px; border-radius: 6px; font-size: 12px; font-family: {paleta.MONO};
            background: {paleta.REJILLA}; border: 1px solid {paleta.BORDE}; color: {paleta.TINTA}; margin: 0 6px 4px 0; }}
.kf-ok {{ background: {paleta.EXITO}22; border-color: {paleta.EXITO}66; color: {paleta.EXITO}; }}
.kf-leyenda {{ display: flex; flex-wrap: wrap; gap: 18px; font-size: 13px; color: {paleta.SUAVE};
               padding: 8px 2px 2px; }}
.kf-leyenda span {{ display: inline-flex; align-items: center; gap: 7px; }}
.kf-leyenda i {{ display: inline-block; width: 14px; height: 14px; border-radius: 3px; }}

/* portada */
.kf-hero {{ border: 1px solid {paleta.BORDE}; border-radius: 16px; padding: 40px 40px 34px;
            background: radial-gradient(ellipse at 85% 0%, {paleta.ALGORITMO['bellman_ford']}33, transparent 55%),
                        radial-gradient(ellipse at 0% 100%, {paleta.ALGORITMO['bfs']}26, transparent 50%),
                        {paleta.TARJETA}; }}
.kf-hero h1 {{ font-size: 2.6rem !important; line-height: 1.1; margin: 14px 0 12px; max-width: 760px; }}
.kf-hero h1 span {{ background: linear-gradient(90deg, {paleta.ALGORITMO['bfs']}, {paleta.ALGORITMO['bellman_ford']},
                    {paleta.ALGORITMO['edmonds_karp']}); -webkit-background-clip: text; background-clip: text;
                    color: transparent; }}
.kf-hero p {{ color: {paleta.SUAVE}; font-size: 1.05rem; max-width: 640px; }}
.kf-modulo {{ background: {paleta.TARJETA}; border: 1px solid {paleta.BORDE}; border-radius: 12px; padding: 18px;
              border-top: 3px solid var(--acento); min-height: 168px; }}
.kf-modulo .kf-mono {{ font-size: 12px; color: var(--acento); }}
.kf-modulo b {{ display: block; font-size: 1.05rem; margin: 6px 0; }}
[data-testid="stPageLink"] a {{ border: 1px solid {paleta.BORDE}; border-radius: 8px; padding: 4px 12px;
                                background: {paleta.REJILLA}; }}
[data-testid="stPageLink"] a:hover {{ border-color: {paleta.ACENTO}; }}
.kf-pie {{ margin-top: 48px; padding: 16px 0; border-top: 1px solid {paleta.BORDE}; font-size: 12px;
           color: {paleta.SUAVE}; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 8px; }}
.kf-pie a {{ color: {paleta.SUAVE}; }}
table {{ font-size: 13px; }}
thead tr th {{ background: {paleta.REJILLA} !important; }}
</style>
""", unsafe_allow_html=True)


def encabezado(modulo, titulo, sub):
    """Encabezado de página: ruta tipo consola, título, estado del motor y subtítulo."""
    motor = "Pyodide · en tu navegador" if EN_NAVEGADOR else "Python local"
    st.markdown(f"<div class='kf-estado'><span class='kf-punto'></span>Motor: {motor}</div>"
                f"<div class='kf-ruta'>kivaflow / <b>{modulo}</b></div>", unsafe_allow_html=True)
    st.markdown(f"# {titulo}")
    st.markdown(f"<div class='kf-sub'>{sub}</div>", unsafe_allow_html=True)


def seccion(titulo, nota=""):
    st.markdown(f"<div class='kf-seccion'><b>{titulo}</b><span>{nota}</span></div>", unsafe_allow_html=True)


def panel(clave, titulo=""):
    """Panel con fondo de tarjeta (el estilo lo da la clase st-key-panel-…)."""
    caja = st.container(border=True, key=f"panel-{clave}")
    if titulo:
        caja.markdown(f"<div class='kf-titulo-panel'>{titulo}</div>", unsafe_allow_html=True)
    return caja


def tarjeta(etiqueta, valor, nota="", sufijo="", acento=paleta.ACENTO):
    st.markdown(f"<div class='kf-card acento' style='--acento:{acento}'><div class='kf-etq'>{etiqueta}</div>"
                f"<div class='kf-num'>{valor}<small>{sufijo}</small></div><div class='kf-nota'>{nota}</div></div>",
                unsafe_allow_html=True)


def fila_metricas(items, acento=paleta.ACENTO):
    """Fila compacta de métricas [(etiqueta, valor), ...] que no se corta en columnas angostas."""
    celdas = "".join(f"<div class='kf-card acento' style='padding:10px 12px;--acento:{acento}'>"
                     f"<div class='kf-etq'>{e}</div><div class='kf-num' style='font-size:1.35rem'>{v}</div></div>"
                     for e, v in items)
    st.markdown(f"<div style='display:grid;grid-template-columns:repeat({len(items)},1fr);gap:8px'>{celdas}</div>",
                unsafe_allow_html=True)


def leyenda(items):
    """Leyenda bajo el lienzo [(color, texto, forma)], forma: 'cuadro', 'anillo', 'punto' o 'linea'."""
    estilos = {"cuadro": "background:{c}", "punto": "background:{c};border-radius:50%",
               "anillo": "border:3px solid {c};border-radius:50%;width:10px;height:10px",
               "linea": "background:{c};height:4px;width:18px;border-radius:2px"}
    celdas = "".join(f"<span><i style='{estilos[f].format(c=c)}'></i>{t}</span>" for c, t, f in items)
    st.markdown(f"<div class='kf-leyenda'>{celdas}</div>", unsafe_allow_html=True)


def leyenda_busqueda(algoritmos):
    items = [(paleta.INICIO, "Inicio", "punto"), (paleta.DESTINO, "Destino", "anillo")]
    for a in algoritmos:
        items += [(paleta.ALGORITMO_CLARO[a], f"Visitado · {NOMBRE[a]}", "cuadro"),
                  (paleta.ALGORITMO[a], f"Ruta · {NOMBRE[a]}", "linea")]
    items += [(paleta.FRENTE, "Paso actual", "cuadro"), (paleta.CONGESTION_SUAVE["Media"], "Congestión media", "linea"),
              (paleta.CONGESTION_SUAVE["Alta"], "Congestión alta", "linea")]
    leyenda(items)


def barras(titulo, valores, formato="{:,.0f}", nota="menos es mejor"):
    """Barras horizontales HTML: {algoritmo: valor}."""
    maximo = max(valores.values()) or 1
    filas = "".join(
        f"<div class='kf-barra'><span>{NOMBRE[a]}</span><div class='pista'><div class='lleno' style='width:"
        f"{100 * v / maximo:.1f}%;background:{paleta.ALGORITMO[a]}'></div></div>"
        f"<span class='valor'>{formato.format(v).replace(',', ' ')}</span></div>"
        for a, v in valores.items())
    st.markdown(f"<div style='margin-bottom:14px'><div style='display:flex;justify-content:space-between'>"
                f"<b style='font-size:13px'>{titulo}</b><span class='kf-nota'>{nota}</span></div>{filas}</div>",
                unsafe_allow_html=True)


# ---------- datos (se calculan una vez y quedan en caché) ----------

@st.cache_resource
def datos():
    popularidad, fuente = grafo.leer_popularidad()
    return grafo.leer_nodos(), grafo.leer_aristas(), popularidad, fuente


@st.cache_resource
def estructuras(perfil):
    _, aristas, _, _ = datos()
    ady = grafo.adyacencia(aristas, perfil)
    return ady, grafo.lista_de_aristas(ady)


@st.cache_resource
def flujo_dataset(origen, destino):
    nodos, aristas, _, _ = datos()
    return ek.entre_zonas(grafo.capacidades(aristas), nodos, origen, destino)


@st.cache_resource
def figura_historia():
    nodos, aristas, _, _ = datos()
    ady, _ = estructuras("punta")
    return interactivo.historia(nodos, aristas, ady, "22-39", "08-03")


def medir_memoria(funcion):
    """Memoria pico (KB) de una llamada con tracemalloc. En el navegador no es confiable: no se mide."""
    if EN_NAVEGADOR:
        return None
    try:
        tracemalloc.start()
        funcion()
        return round(tracemalloc.get_traced_memory()[1] / 1024)
    finally:
        tracemalloc.stop()


nodos, aristas, popularidad, fuente = datos()
IDS = list(nodos)
por_par = {frozenset((a["Nodo_Origen"], a["Nodo_Destino"])): a for a in aristas}
for clave, valor in {"inicio": "22-39", "destinos": ["05-05", "40-10", "10-30"], "sel_k": 0, "videos": {},
                     "turno": None, "verif_vivo": None, "perfil": "punta", "regresar": False}.items():
    ss.setdefault(clave, valor)


def selector_puntos(clave):
    """Panel de control a la izquierda y mapa clicable a la derecha. Deja los puntos en ss.inicio y ss.destinos."""
    control, lienzo = st.columns([1, 3.2])
    with control, panel(f"control-{clave}", "Configuración"):
        modo = st.segmented_control("El clic marca", ["Inicio", "Destino"], default="Inicio", key=f"modo-{clave}")
        ss.perfil = st.segmented_control("Hora", ["punta", "valle"], default=ss.perfil, key=f"hora-{clave}") or "punta"
        n = st.number_input("Destinos", 1, 10, max(1, len(ss.destinos)), key=f"n-{clave}")
        ss.regresar = st.toggle("Volver al inicio", value=ss.regresar, key=f"reg-{clave}")
        if st.button("Puntos al azar", key=f"azar-{clave}", icon=":material/shuffle:", use_container_width=True):
            rng = random.Random()
            ss.inicio = rng.choice(IDS)
            ss.destinos = rng.sample([x for x in IDS if x != ss.inicio], n)
            ss.videos = {}
        chips = "".join(f"<span class='kf-chip'>{d}</span>" for d in ss.destinos) or "—"
        st.markdown(f"<div class='kf-etq' style='margin-top:8px'>Inicio</div><span class='kf-chip' style='color:"
                    f"{paleta.INICIO};border-color:{paleta.INICIO}88'>{ss.inicio}</span>"
                    f"<div class='kf-etq' style='margin-top:6px'>Destinos</div>{chips}", unsafe_allow_html=True)
    with lienzo, panel(f"mapa-{clave}"):
        fig = interactivo.mapa(nodos, aristas, ss.inicio, ss.destinos, titulo="Haz clic en una ubicación del almacén")
        fig.update_layout(height=470, showlegend=False)
        evento = st.plotly_chart(fig, key=f"mapa-{clave}-{ss.sel_k}", on_select="rerun", selection_mode="points",
                                 use_container_width=True, config={"scrollZoom": False, "displayModeBar": False})
        leyenda([(paleta.INICIO, "Inicio", "punto"), (paleta.DESTINO, "Destino", "anillo")]
                + [(c, z, "punto") for z, c in paleta.ZONA.items()])
    puntos = [p for p in (evento.selection.points if evento else []) if p.get("curve_number") == interactivo.NODOS_TRAZA]
    if puntos:
        nodo = IDS[puntos[0]["point_index"]]
        if modo == "Inicio":
            ss.inicio = nodo
        elif nodo in ss.destinos:
            ss.destinos.remove(nodo)
        elif len(ss.destinos) < 10 and nodo != ss.inicio:
            ss.destinos.append(nodo)
        ss.sel_k += 1
        ss.videos = {}
        st.rerun()


def calcular_rutas(algoritmos):
    ady, dirigidas = estructuras(ss.perfil)
    res = {}
    for alg in algoritmos:
        registro = []
        t0 = time.perf_counter()
        r = pedido.ruta_pedido(ady, dirigidas, ss.inicio, ss.destinos, alg, regresar=ss.regresar)
        ms = (time.perf_counter() - t0) * 1000
        pedido.ruta_pedido(ady, dirigidas, ss.inicio, ss.destinos, alg, registro, regresar=ss.regresar)
        kb = medir_memoria(lambda a=alg: pedido.ruta_pedido(ady, dirigidas, ss.inicio, ss.destinos, a,
                                                            regresar=ss.regresar))
        estados = interactivo.estados_busqueda(registro, alg, ss.inicio, ady, len(dirigidas), max_cuadros=300)
        res[alg] = {"r": r, "m": pedido.medir(r["camino"], por_par, ss.perfil), "ms": ms, "kb": kb,
                    "estados": estados, "registro": registro, "trabajo": estados[-1]["trabajo"]}
    return res


def video(fig, clave):
    st.plotly_chart(fig, use_container_width=True, key=clave, config={"displayModeBar": False})


# ======================= PÁGINAS =======================

def inicio():
    v = json.loads((RAIZ / "resultados" / "verificacion.json").read_text(encoding="utf-8"))
    total = sum(d["consultas"] for d in v["algoritmos"].values())
    ok = sum(d["aciertos"] for d in v["algoritmos"].values())
    st.markdown(f"""<div class='kf-hero'>
<span class='kf-chip'>Complejidad Algorítmica · 1ACC0184 · UPC 2026-2</span>
<span class='kf-chip kf-ok'>{ok} / {total} verificadas con NetworkX</span>
<h1>Rutas de picking y cuellos de botella, <span>visualizados paso a paso.</span></h1>
<p>Un almacén tipo Amazon modelado como grafo de 1 800 ubicaciones. Mira a BFS, Bellman-Ford y Edmonds-Karp
recorrerlo con su pseudocódigo en vivo, compáralos sobre los mismos puntos y descubre dónde se atasca el almacén.</p>
</div>""", unsafe_allow_html=True)
    st.write("")
    a, b, c, _ = st.columns([1.2, 1.2, 1.2, 3])
    a.page_link(PAGINAS["explorar"], label="Empezar a explorar", icon=":material/play_arrow:")
    b.page_link(PAGINAS["comparar"], label="Comparar algoritmos", icon=":material/compare_arrows:")
    c.page_link(PAGINAS["simular"], label="Simular un turno", icon=":material/groups:")

    st.write("")
    for col, (etq, val, nota, acento) in zip(st.columns(4), [
            ("Ubicaciones", "1 800", "45 × 40 en tres zonas", paleta.ZONA["Recepción y Almacenamiento"]),
            ("Pasillos", "3 515", "congestión medida con 2 000 pedidos", paleta.CONGESTION["Media"]),
            ("Algoritmos", "3", "BFS · Bellman-Ford · Edmonds-Karp", paleta.ALGORITMO["bellman_ford"]),
            ("Verificado", f"{ok:,}".replace(",", " "), "consultas iguales a NetworkX", paleta.EXITO)]):
        with col:
            tarjeta(etq, val, nota, acento=acento)

    seccion("Módulos", "elige qué quieres ver")
    modulos = [("explorar", "bfs", "01 · paso a paso", "Explorar",
                "Un algoritmo a la vez con su pseudocódigo iluminado, contadores y narración de cada paso."),
               ("comparar", "bellman_ford", "02 · lado a lado", "Comparar",
                "BFS y Bellman-Ford sincronizados por trabajo: caminata, pasillos, cálculo y memoria."),
               ("simular", "edmonds_karp", "03 · turno completo", "Simulación",
                "Operarios moviéndose a la vez, pasillos que se congestionan y el corte mínimo con Edmonds-Karp."),
               ("verificar", None, "04 · evidencia", "Verificación",
                "Los tres algoritmos contra NetworkX, con la opción de volver a verificar en tu navegador.")]
    for col, (k, alg, num, titulo, texto) in zip(st.columns(4), modulos):
        acento = paleta.ALGORITMO[alg] if alg else paleta.EXITO
        col.markdown(f"<div class='kf-modulo' style='--acento:{acento}'><span class='kf-mono'>{num}</span>"
                     f"<b>{titulo}</b><div class='kf-nota'>{texto}</div></div>", unsafe_allow_html=True)
        col.page_link(PAGINAS[k], label=f"Abrir {titulo}", icon=":material/arrow_forward:")

    fig, info = figura_historia()
    seccion("Demo · El operario que recalcula", "dale play")
    texto, lienzo = st.columns([1, 2.6])
    with texto, panel("historia-texto", "Qué pasa"):
        for n, (fase, detalle) in enumerate(zip(interactivo.FASES, [
                "Bellman-Ford explora el almacén con la congestión de hora punta.",
                "Traza la ruta más rápida y el operario empieza a caminar.",
                f"Un robot se avería en {info['bloqueado']}: esa ubicación sale del grafo.",
                f"Recalcula desde {info['desde']}, sin volver a empezar."]), 1):
            st.markdown(f"<span class='kf-chip'>{n}</span><b>{fase}</b><div class='kf-nota' "
                        f"style='margin:2px 0 12px'>{detalle}</div>", unsafe_allow_html=True)
    with lienzo, panel("historia"):
        video(fig, "historia")


def comparar():
    encabezado("comparar", "Comparar algoritmos",
               "Los mismos puntos y la misma congestión: ruta, tiempo de caminata y trabajo de cálculo.")
    selector_puntos("comparar")
    if not (ss.inicio and ss.destinos):
        st.info("Marca un inicio y al menos un destino.")
        return
    res = calcular_rutas(["bfs", "bellman_ford"])
    b, f = res["bfs"], res["bellman_ford"]

    seccion("Resultados", f"{len(ss.destinos)} destinos · hora {ss.perfil}")
    for col, alg in zip(st.columns(2), ["bfs", "bellman_ford"]):
        d = res[alg]
        with col:
            st.markdown(f"<div style='margin-bottom:6px'><b style='color:{paleta.ALGORITMO[alg]}'>■</b> "
                        f"<b>{NOMBRE[alg]}</b> &nbsp;<span class='kf-chip'>tiempo {COMPLEJIDAD[alg][0]}</span>"
                        f"<span class='kf-chip'>espacio {COMPLEJIDAD[alg][1]}</span></div>", unsafe_allow_html=True)
            fila_metricas([("Caminata", f"{d['m']['tiempo_s']} s"), ("Pasillos", d["m"]["pasillos"]),
                           ("Cálculo", f"{d['ms']:.1f} ms"),
                           ("Memoria pico", f"{d['kb']} KB" if d["kb"] is not None else "—")],
                          acento=paleta.ALGORITMO[alg])

    seccion("Reproducción sincronizada", "el reloj común es el trabajo (aristas revisadas)")
    izq, der = st.columns([2.6, 1])
    with izq, panel("video-comparar"):
        clave = ("comparar", ss.inicio, tuple(ss.destinos), ss.perfil, ss.regresar)
        if clave not in ss.videos:
            ss.videos[clave] = interactivo.comparar(nodos, aristas, {a: res[a]["estados"] for a in res},
                                                    ss.inicio, ss.destinos)
        video(ss.videos[clave], "video-comparar")
        leyenda_busqueda(["bfs", "bellman_ford"])
    with der, panel("metricas-comparar", "Métricas"):
        barras("Tiempo de caminata (s)", {a: res[a]["m"]["tiempo_s"] for a in res}, "{:.1f}")
        barras("Aristas revisadas", {a: res[a]["trabajo"] for a in res})
        barras("Tiempo de cálculo (ms)", {a: res[a]["ms"] for a in res}, "{:.1f}", "depende de la PC")
        ahorro = b["m"]["tiempo_s"] - f["m"]["tiempo_s"]
        veces = f["trabajo"] / max(b["trabajo"], 1)
        texto = (f"Bellman-Ford ahorra <b>{ahorro:.1f} s</b> de caminata ({100 * ahorro / b['m']['tiempo_s']:.0f} %) "
                 f"esquivando la congestión, pero revisa <b>{veces:.0f} veces</b> más aristas que BFS."
                 if ahorro > 0.05 else
                 f"Las dos rutas cuestan lo mismo (el camino corto no estaba congestionado), pero Bellman-Ford "
                 f"revisó <b>{veces:.0f} veces</b> más aristas.")
        st.markdown(f"<div class='kf-etq'>Conclusión</div><div class='kf-conclusion'>{texto}</div>",
                    unsafe_allow_html=True)
        st.markdown("<div class='kf-nota' style='margin-top:10px'>En cada cuadro los dos llevan, como mucho, la "
                    "misma cantidad de trabajo: por eso BFS termina casi de inmediato."
                    + (" La memoria pico se mide en la versión local (python app.py)." if b["kb"] is None else "")
                    + "</div>", unsafe_allow_html=True)


def explorar():
    encabezado("explorar", "Explorar paso a paso",
               "Un algoritmo, paso por paso, con su pseudocódigo en vivo: la línea activa se ilumina y cada "
               "contador muestra cuántas veces se ejecutó.")
    with panel("barra-explorar"):
        c1, c2, c3 = st.columns([2, 1.4, 1.4])
        alg = c1.segmented_control("Algoritmo", ["bfs", "bellman_ford", "edmonds_karp"], default="bfs",
                                   format_func=NOMBRE.get, key="alg-explorar") or "bfs"
        if alg == "edmonds_karp":
            o = c2.selectbox("Desde la zona", ZONAS, index=0)
            d = c3.selectbox("Hasta la zona", [z for z in ZONAS if z != o], index=len(ZONAS) - 2)
        else:
            c2.markdown(f"<div class='kf-etq'>Complejidad</div><span class='kf-chip'>tiempo {COMPLEJIDAD[alg][0]}"
                        f"</span><span class='kf-chip'>espacio {COMPLEJIDAD[alg][1]}</span>", unsafe_allow_html=True)
            c3.markdown(f"<div class='kf-etq'>Puntos</div><span class='kf-chip' style='color:{paleta.INICIO}'>"
                        f"{ss.inicio}</span><span class='kf-chip'>{len(ss.destinos)} destinos</span>"
                        f"<span class='kf-chip'>{ss.perfil}</span>", unsafe_allow_html=True)
    if alg == "edmonds_karp":
        clave = ("ek", o, d)
        if clave not in ss.videos:
            pasos = []
            _, _, cuellos, _ = ek.entre_zonas(grafo.capacidades(aristas), nodos, o, d, pasos)
            ss.videos[clave] = interactivo.explorar_flujo(nodos, aristas, interactivo.estados_flujo(pasos, cuellos))
        with panel("video-ek"):
            video(ss.videos[clave], "video-ek")
            leyenda([(paleta.SUAVE, "Pasillo con flujo", "linea"), (paleta.ALGORITMO["bfs"], "Camino de aumento", "linea"),
                     (paleta.ALGORITMO["edmonds_karp"], "Corte mínimo", "linea")])
        st.markdown("<span class='kf-nota'>Edmonds-Karp no busca una ruta entre dos puntos: mide cuántos operarios "
                    "por minuto caben de una zona a otra (capacidad por pasillo: baja 3, media 2, alta 1).</span>",
                    unsafe_allow_html=True)
        return
    with st.expander("Cambiar los puntos (inicio, destinos y hora)", icon=":material/tune:"):
        selector_puntos("explorar")
    if not (ss.inicio and ss.destinos):
        st.info("Marca un inicio y al menos un destino.")
        return
    clave = ("explorar", alg, ss.inicio, tuple(ss.destinos), ss.perfil, ss.regresar)
    if clave not in ss.videos:
        ady, dirigidas = estructuras(ss.perfil)
        registro = []
        pedido.ruta_pedido(ady, dirigidas, ss.inicio, ss.destinos, alg, registro, regresar=ss.regresar)
        estados = interactivo.estados_busqueda(registro, alg, ss.inicio, ady, len(dirigidas))
        ss.videos[clave] = interactivo.explorar(nodos, aristas, estados, alg, ss.inicio, ss.destinos)
    with panel("video-explorar"):
        video(ss.videos[clave], "video-explorar")
        leyenda_busqueda([alg])


def simular():
    encabezado("simulación", "Simulación de un turno",
               "Varios operarios a la vez: los pasillos más cruzados se congestionan, baja su capacidad y "
               "Edmonds-Karp encuentra dónde se atasca el almacén.")
    control, tablero = st.columns([1, 3.2])
    with control, panel("control-sim", "Parámetros"):
        ruta_ops = st.segmented_control("Los operarios usan", ["bfs", "bellman_ford"], default="bfs",
                                        format_func=NOMBRE.get) or "bfs"
        n_ops = st.slider("Operarios", 5, 15 if ruta_ops == "bellman_ford" else 60,
                          10 if ruta_ops == "bellman_ford" else 30)
        max_prod = st.slider("Productos máx. por pedido", 1, 5, 3)
        hora = st.segmented_control("Hora", ["punta", "valle"], default="punta", key="hora-sim") or "punta"
        z_origen = st.selectbox("Flujo desde", ZONAS, index=0)
        z_destino = st.selectbox("hasta", [z for z in ZONAS if z != z_origen], index=len(ZONAS) - 2)
        semilla = st.number_input("Semilla", 0, 9999, 1)
        if st.button("Simular turno", type="primary", icon=":material/play_arrow:", use_container_width=True):
            with st.spinner("Calculando rutas, congestión y flujo máximo…"):
                ady_s, dir_s = estructuras(hora)
                ops = simulacion.turno(nodos, ady_s, dir_s, popularidad, n_ops, max_prod, ruta_ops, semilla)
                pasos = []
                res = simulacion.congestion_y_flujo(nodos, aristas, ops, z_origen, z_destino, pasos)
                ss.turno = {"ops": ops, "res": res, "origen": z_origen, "destino": z_destino,
                            "video_turno": interactivo.animacion_turno(nodos, aristas, ops),
                            "video_flujo": interactivo.explorar_flujo(nodos, aristas,
                                                                      interactivo.estados_flujo(pasos, res["cuellos"]),
                                                                      res["niveles"])}
    with tablero:
        if not ss.turno:
            with panel("vacio-sim"):
                st.markdown("<div style='padding:80px 0;text-align:center'><b>Sin simulación todavía</b>"
                            "<div class='kf-nota'>Ajusta los parámetros a la izquierda y presiona "
                            "<b>Simular turno</b>.</div></div>", unsafe_allow_html=True)
            return
        tr = ss.turno
        res = tr["res"]
        base_valor = flujo_dataset(tr["origen"], tr["destino"])[0]
        c = st.columns(4)
        with c[0]:
            tarjeta("Operarios", len(tr["ops"]), "un pedido cada uno", acento=paleta.INICIO)
        with c[1]:
            tarjeta("Pasillos usados", len(res["uso"]), f"de {len(aristas)}", acento=paleta.ALGORITMO["bfs"])
        with c[2]:
            tarjeta("Pasillo más cruzado", max(res["uso"].values()), "veces en el turno",
                    acento=paleta.CONGESTION["Alta"])
        with c[3]:
            tarjeta("Flujo máximo", res["valor"], f"operarios/min · sin el turno: {base_valor}",
                    acento=paleta.ALGORITMO["edmonds_karp"])
        st.write("")
        t1, t2 = st.tabs(["El turno", f"Edmonds-Karp · {tr['origen']} → {tr['destino']}"])
        with t1, panel("video-turno"):
            video(tr["video_turno"], "video-turno")
            leyenda([(paleta.TINTA, "Operario", "punto"), (paleta.CONGESTION["Media"], "Pasillo cruzado", "punto"),
                     (paleta.CONGESTION["Alta"], "Muy cruzado", "punto")])
        with t2, panel("video-flujo"):
            video(tr["video_flujo"], "video-flujo")
            leyenda([(paleta.SUAVE, "Pasillo con flujo", "linea"), (paleta.ALGORITMO["bfs"], "Camino de aumento", "linea"),
                     (paleta.ALGORITMO["edmonds_karp"], "Corte mínimo", "linea")])


def resultados():
    encabezado("resultados", "Resultados del experimento",
               "360 pedidos: BFS contra Bellman-Ford en hora valle y punta, y el corte mínimo entre zonas.")
    resumen = (RAIZ / "resultados" / "resumen.md").read_text(encoding="utf-8")
    t1, t2 = st.tabs(["Tablas", "Figuras"])
    with t1, panel("tablas"):
        st.markdown("\n".join("#" + l if l.startswith("## ") else l for l in resumen.splitlines()
                               if not l.startswith("![") and not l.startswith("# ")))
    with t2:
        c1, c2 = st.columns(2)
        with c1, panel("fig-ruta", "Ruta de ejemplo"):
            st.image(str(RAIZ / "resultados" / "ruta_ejemplo.png"))
        with c2, panel("fig-corte", "Cuellos de botella"):
            st.image(str(RAIZ / "resultados" / "cuellos_de_botella.png"))


def verificar():
    encabezado("verificación", "Verificación contra NetworkX",
               "Nuestros algoritmos contra la librería de grafos de referencia: la evidencia detrás de las cifras "
               "del informe.")
    v = json.loads((RAIZ / "resultados" / "verificacion.json").read_text(encoding="utf-8"))
    c = st.columns(4)
    for col, (alg, d) in zip(c, v["algoritmos"].items()):
        estado = "PASA" if d["aciertos"] == d["consultas"] else "REVISAR"
        with col:
            tarjeta(f"{NOMBRE[alg]} &nbsp;<span class='kf-chip kf-ok'>{estado}</span>", d["aciertos"],
                    f"consultas iguales · error máx. {d['error_max']:.1e}", f" / {d['consultas']}",
                    acento=paleta.ALGORITMO[alg])
    with c[3]:
        tarjeta("Verificado el", v["fecha"], f"Python {v['python']} · NetworkX {v['networkx']} · {v['segundos']} s",
                acento=paleta.EXITO)
    seccion("Detalle", f"{v['sistema']} · semilla {v['semilla']}")
    with panel("tabla-verif"):
        st.markdown("""
| Algoritmo | Consultas | Iguales a NetworkX | Error máximo | Criterio |
|---|---|---|---|---|
""" + "\n".join(f"| {NOMBRE[a]} | {d['consultas']} | {d['aciertos']} | {d['error_max']:.1e} | {d['criterio']} |"
                for a, d in v["algoritmos"].items()) + """

<span class='kf-nota'>Se reproduce con `python scripts/verificar.py`. Los tiempos de cálculo de la app son
descriptivos: dependen de la PC.</span>
""", unsafe_allow_html=True)
    seccion("Verificar ahora", "una muestra más chica, aquí mismo y con otra semilla")
    with panel("verif-vivo"):
        if st.button("Verificar 40 + 20 + 6 consultas", type="primary", icon=":material/verified:"):
            barra = st.progress(0.0)
            ss.verif_vivo = verificacion.verificar(nodos, aristas, 40, 10, semilla=random.randrange(10_000),
                                                   progreso=lambda p: barra.progress(min(p, 1.0)))
        if ss.verif_vivo:
            vv = ss.verif_vivo
            st.success(" · ".join(f"{NOMBRE[a]} {d['aciertos']}/{d['consultas']}" for a, d in vv["algoritmos"].items())
                       + f" — {vv['segundos']} s en {vv['sistema']}")


def acerca():
    encabezado("acerca", "Acerca del proyecto",
               "Trabajo del curso 1ACC0184 Complejidad Algorítmica (UPC, 2026-2). Caso 2: gestión de almacenes "
               "inteligentes (Amazon). Todo se calcula en Python; esta página corre dentro de tu navegador.")
    seccion("Algoritmos")
    algs = [("bfs", "No considera pesos", "Recorridos y búsquedas en grafos", "Cormen et al. (2022)",
             "Ruta con menos pasillos; línea base."),
            ("bellman_ford", "Óptimo con pesos", "Bellman-Ford", "Bellman (1958)",
             "Ruta de menor tiempo con la congestión de cada pasillo."),
            ("edmonds_karp", "Óptimo (flujo)", "Flujo máximo en redes (Ford-Fulkerson)", "Edmonds y Karp (1972)",
             "Capacidad entre zonas y corte mínimo (cuellos de botella).")]
    for col, (a, opt, tec, ref, para) in zip(st.columns(3), algs):
        col.markdown(f"""<div class='kf-modulo' style='--acento:{paleta.ALGORITMO[a]}'>
<span class='kf-mono'>{COMPLEJIDAD[a][0]} tiempo · {COMPLEJIDAD[a][1]} espacio</span>
<b>{NOMBRE[a]}</b><span class='kf-chip'>{opt}</span>
<p class='kf-nota' style='margin-top:8px'>{para}</p>
<div class='kf-etq'>Técnica del enunciado</div><div style='font-size:14px'>{tec}</div>
<div class='kf-etq' style='margin-top:8px'>Referencia</div><div style='font-size:14px'>{ref}</div></div>""",
                     unsafe_allow_html=True)
    seccion("El modelo")
    textos = [("Datos", """Cuadrícula sintética de 45 × 40 ubicaciones (1 800 nodos, 3 515 pasillos) inspirada en
los almacenes robóticos Kiva (Wurman et al., 2008): Amazon no publica sus planos y los datasets públicos de
*order picking* no traen topología. La congestión de cada pasillo se **mide** simulando 2 000 pedidos (popularidad
Zipf o pedidos reales de *Instacart Market Basket Analysis*, Kaggle) y partiendo los pasillos en tercios."""),
              ("Reglas del modelo", """Cada ubicación es un vértice; cada pasillo une dos vecinas (4 direcciones) y
mide 1,2 m. En hora punta un pasillo de congestión media pesa ×1,25 y uno alta ×1,6 (en valle ×1,1 y ×1,25). Para
el flujo, cada pasillo deja pasar 3, 2 o 1 operarios por minuto según su congestión. El orden de visita de varios
destinos es el del vecino más cercano (heurística voraz): el óptimo sería el problema del viajero, que es
NP-difícil."""),
              ("Uso de IA", f"""El código se escribió con asistencia de Claude (Anthropic) y el grupo lo revisó y
lo verificó (ver *Verificación*); está declarado en la bitácora del informe. Código: [{REPO}]({REPO}).""")]
    for col, (titulo, texto) in zip(st.columns(3), textos):
        with col, panel(f"modelo-{titulo}", titulo):
            st.markdown(texto)


PAGINAS = {
    "inicio": st.Page(inicio, title="Inicio", icon=":material/home:", default=True),
    "explorar": st.Page(explorar, title="Explorar", icon=":material/explore:"),
    "comparar": st.Page(comparar, title="Comparar", icon=":material/compare_arrows:"),
    "simular": st.Page(simular, title="Simulación", icon=":material/groups:"),
    "resultados": st.Page(resultados, title="Resultados", icon=":material/bar_chart:"),
    "verificar": st.Page(verificar, title="Verificación", icon=":material/verified:"),
    "acerca": st.Page(acerca, title="Acerca", icon=":material/info:"),
}
nav = st.navigation(list(PAGINAS.values()), position="top")
nav.run()
st.markdown(f"<div class='kf-pie'><span><b style='color:{paleta.TINTA}'>KivaFlow</b> · laboratorio de rutas · "
            f"{'demanda Instacart' if fuente == 'instacart' else 'demanda sintética'}</span>"
            f"<span>Complejidad Algorítmica · UPC 2026-2 · <a href='{REPO}' target='_blank'>código</a></span></div>",
            unsafe_allow_html=True)
