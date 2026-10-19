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

# ---------- estilo «Papel y tinta» ----------
st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Inter:wght@400;500;600&family=JetBrains+Mono&display=swap');
html, body, p, li, label, input, textarea, button p, .stMarkdown {{ font-family: {paleta.SANS}; }}
[data-testid="stSidebarNav"] {{ display: none; }}
section[data-testid="stSidebar"] [data-testid="stPageLink"] a {{ border-radius: 10px; padding: 2px 6px; }}
.kf-seccion {{ font-size: 11px; letter-spacing: .1em; text-transform: uppercase; color: {paleta.SUAVE};
              margin: 18px 0 4px 4px; }}
h1, h2, h3, .kf-serif {{ font-family: {paleta.SERIF} !important; font-weight: 400 !important; letter-spacing: -0.01em; }}
h1 {{ font-size: 2.3rem !important; }}
h1 em, h2 em, h3 em {{ font-style: italic; color: {paleta.SUAVE}; }}
.block-container {{ padding-top: 2.2rem; max-width: 1320px; }}
.kf-sub {{ color: {paleta.SUAVE}; margin-top: -0.6rem; margin-bottom: 1.2rem; }}
.kf-card {{ background: {paleta.TARJETA}; border: 1px solid {paleta.BORDE}; border-radius: 14px; padding: 16px 18px;
           height: 100%; }}
.kf-etq {{ font-size: 11px; letter-spacing: .08em; text-transform: uppercase; color: {paleta.SUAVE}; }}
.kf-num {{ font-family: {paleta.SERIF}; font-size: 2.1rem; line-height: 1.1; margin: 4px 0; }}
.kf-num small {{ font-size: 1rem; color: {paleta.SUAVE}; }}
.kf-nota {{ font-size: 13px; color: {paleta.SUAVE}; }}
.kf-conclusion {{ background: #FBF3E2; border: 1px solid #EED9AE; border-radius: 12px; padding: 12px 16px;
                  font-size: 14px; }}
.kf-barra {{ display: grid; grid-template-columns: 110px 1fr 90px; align-items: center; gap: 10px;
             font-size: 13px; margin: 6px 0; }}
.kf-barra .pista {{ background: {paleta.REJILLA}; border-radius: 4px; height: 8px; }}
.kf-barra .lleno {{ height: 8px; border-radius: 4px; }}
.kf-barra .valor {{ text-align: right; font-variant-numeric: tabular-nums; }}
.kf-paso {{ font-family: {paleta.SERIF}; font-size: 2rem; color: {paleta.BORDE}; float: right; }}
.kf-chip {{ display: inline-block; padding: 2px 9px; border-radius: 999px; font-size: 12px;
            background: {paleta.REJILLA}; color: {paleta.TINTA}; margin-right: 6px; }}
section[data-testid="stSidebar"] .kf-marca {{ font-family: {paleta.SERIF}; font-size: 1.6rem; }}
[data-testid="stMetricValue"] {{ font-family: {paleta.SERIF}; }}
</style>
""", unsafe_allow_html=True)


def encabezado(titulo, cursiva, sub):
    st.markdown(f"# {titulo} *{cursiva}*")
    st.markdown(f"<div class='kf-sub'>{sub}</div>", unsafe_allow_html=True)


def tarjeta(etiqueta, valor, nota="", sufijo=""):
    st.markdown(f"<div class='kf-card'><div class='kf-etq'>{etiqueta}</div>"
                f"<div class='kf-num'>{valor}<small>{sufijo}</small></div><div class='kf-nota'>{nota}</div></div>",
                unsafe_allow_html=True)


def fila_metricas(items):
    """Fila compacta de métricas [(etiqueta, valor), ...] que no se corta en columnas angostas."""
    celdas = "".join(f"<div class='kf-card' style='padding:10px 12px'><div class='kf-etq'>{e}</div>"
                     f"<div class='kf-num' style='font-size:1.45rem'>{v}</div></div>" for e, v in items)
    st.markdown(f"<div style='display:grid;grid-template-columns:repeat({len(items)},1fr);gap:8px'>{celdas}</div>",
                unsafe_allow_html=True)


def barras(titulo, valores, formato="{:,.0f}", nota="menos es mejor"):
    """Barras horizontales HTML: {algoritmo: valor}."""
    maximo = max(valores.values()) or 1
    filas = "".join(
        f"<div class='kf-barra'><span>{NOMBRE[a]}</span><div class='pista'><div class='lleno' style='width:"
        f"{100 * v / maximo:.1f}%;background:{paleta.ALGORITMO[a]}'></div></div>"
        f"<span class='valor'>{formato.format(v).replace(',', ' ')}</span></div>"
        for a, v in valores.items())
    st.markdown(f"<div style='margin-bottom:14px'><div style='display:flex;justify-content:space-between'>"
                f"<b style='font-size:14px'>{titulo}</b><span class='kf-nota'>{nota}</span></div>{filas}</div>",
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
    """Controles + mapa clicable. Deja los puntos en ss.inicio y ss.destinos."""
    c1, c2, c3, c4, c5 = st.columns([2.2, 2.2, 1.6, 1.4, 1])
    modo = c1.segmented_control("El clic marca", ["Inicio", "Destino"], default="Inicio", key=f"modo-{clave}")
    ss.perfil = c2.segmented_control("Hora", ["punta", "valle"], default=ss.perfil, key=f"hora-{clave}") or "punta"
    ss.regresar = c3.toggle("Volver al inicio", value=ss.regresar, key=f"reg-{clave}")
    n = c4.number_input("Destinos", 1, 10, max(1, len(ss.destinos)), key=f"n-{clave}")
    c5.write("")
    if c5.button("Al azar", key=f"azar-{clave}", use_container_width=True):
        rng = random.Random()
        ss.inicio = rng.choice(IDS)
        ss.destinos = rng.sample([x for x in IDS if x != ss.inicio], n)
        ss.videos = {}
    fig = interactivo.mapa(nodos, aristas, ss.inicio, ss.destinos, titulo="Haz clic en una ubicación del almacén")
    fig.update_layout(height=470, showlegend=False)
    evento = st.plotly_chart(fig, key=f"mapa-{clave}-{ss.sel_k}", on_select="rerun", selection_mode="points",
                             use_container_width=True, config={"scrollZoom": False, "displayModeBar": False})
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
    chips = "".join(f"<span class='kf-chip'>{d}</span>" for d in ss.destinos) or "—"
    st.markdown(f"<span class='kf-nota'>Inicio</span> <span class='kf-chip' style='background:{paleta.TINTA};"
                f"color:white'>{ss.inicio}</span> &nbsp; <span class='kf-nota'>Destinos</span> {chips}",
                unsafe_allow_html=True)


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


# ======================= PÁGINAS =======================

def inicio():
    encabezado("Bienvenido a", "KivaFlow",
               "Un laboratorio de rutas de picking sobre un almacén tipo Amazon modelado como grafo. "
               "Proyecto de Complejidad Algorítmica (UPC, 2026-2).")
    izq, der = st.columns([2, 3])
    with izq:
        st.markdown(f"""<div class='kf-card' style='background:#FBF3E2;border-color:#EED9AE;padding:28px'>
<div class='kf-etq'>Rutas · congestión · capacidad</div>
<h2 style='font-size:2.4rem;line-height:1.15;margin:18px 0'>Encuentra la ruta, <em>entiende la congestión.</em></h2>
<p style='color:{paleta.SUAVE}'>Compara BFS y Bellman-Ford sobre los mismos puntos, mira cada paso con su
pseudocódigo y descubre con Edmonds-Karp dónde se atasca el almacén.</p></div>""", unsafe_allow_html=True)
        st.write("")
        a, b = st.columns(2)
        a.page_link(PAGINAS["comparar"], label="Comparar algoritmos", icon=":material/compare:")
        b.page_link(PAGINAS["explorar"], label="Explorar paso a paso", icon=":material/explore:")
    with der:
        fig, info = figura_historia()
        st.markdown(f"<b class='kf-serif' style='font-size:1.25rem'>El operario que recalcula</b> "
                    f"<span class='kf-nota'>— dale play: un robot se avería en {info['bloqueado']} a mitad de "
                    f"camino y Bellman-Ford recalcula desde {info['desde']}, sin volver a empezar.</span>",
                    unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True, key="historia", config={"displayModeBar": False})

    v = json.loads((RAIZ / "resultados" / "verificacion.json").read_text(encoding="utf-8"))
    total = sum(d["consultas"] for d in v["algoritmos"].values())
    ok = sum(d["aciertos"] for d in v["algoritmos"].values())
    c = st.columns(4)
    with c[0]:
        tarjeta("Ubicaciones", "1 800", "45 × 40 en tres zonas (585 / 630 / 585)")
    with c[1]:
        tarjeta("Pasillos", "3 515", "congestión medida simulando 2 000 pedidos")
    with c[2]:
        tarjeta("Algoritmos", "3", "BFS · Bellman-Ford · Edmonds-Karp")
    with c[3]:
        tarjeta("Verificado", f"{ok:,}".replace(",", " "), f"de {total} consultas iguales a NetworkX", f" / {total}")
    st.write("")
    pasos = [("01", "Elige los puntos", "Clic en el mapa o al azar: inicio y hasta 10 destinos en cualquier zona."),
             ("02", "Mira al algoritmo pensar", "El pseudocódigo se ilumina línea a línea mientras el almacén se explora."),
             ("03", "Compara y decide", "Tiempo de caminata contra trabajo de cálculo: el trade-off, con números.")]
    for col, (n, t, d) in zip(st.columns(3), pasos):
        col.markdown(f"<div class='kf-card'><span class='kf-paso'>{n}</span><b>{t}</b>"
                     f"<p class='kf-nota' style='margin-top:6px'>{d}</p></div>", unsafe_allow_html=True)


def comparar():
    encabezado("Comparar", "dos caminos", "Los mismos puntos y la misma congestión: ruta, tiempo y trabajo de cálculo.")
    selector_puntos("comparar")
    if not (ss.inicio and ss.destinos):
        st.info("Marca un inicio y al menos un destino.")
        return
    res = calcular_rutas(["bfs", "bellman_ford"])
    b, f = res["bfs"], res["bellman_ford"]

    cols = st.columns(2)
    for col, alg in zip(cols, ["bfs", "bellman_ford"]):
        d = res[alg]
        with col:
            st.markdown(f"<h3 style='margin-bottom:4px'>{NOMBRE[alg]} <span class='kf-chip'>"
                        f"{COMPLEJIDAD[alg][0]}</span><span class='kf-chip'>espacio {COMPLEJIDAD[alg][1]}</span></h3>",
                        unsafe_allow_html=True)
            fila_metricas([("Caminata", f"{d['m']['tiempo_s']} s"), ("Pasillos", d["m"]["pasillos"]),
                           ("Cálculo", f"{d['ms']:.1f} ms"),
                           ("Memoria pico", f"{d['kb']} KB" if d["kb"] is not None else "—")])

    izq, der = st.columns([3, 2])
    with der:
        st.markdown("<div class='kf-card'>", unsafe_allow_html=True)
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
        st.markdown(f"<div class='kf-conclusion'>{texto}</div></div>", unsafe_allow_html=True)
        if res["bfs"]["kb"] is None:
            st.markdown("<span class='kf-nota'>La memoria pico se mide en la versión local (python app.py); "
                        "en el navegador no es confiable.</span>", unsafe_allow_html=True)
    with izq:
        clave = ("comparar", ss.inicio, tuple(ss.destinos), ss.perfil, ss.regresar)
        if clave not in ss.videos:
            ss.videos[clave] = interactivo.comparar(nodos, aristas, {a: res[a]["estados"] for a in res},
                                                    ss.inicio, ss.destinos)
        st.plotly_chart(ss.videos[clave], use_container_width=True, key="video-comparar",
                        config={"displayModeBar": False})
        st.markdown("<span class='kf-nota'>El reloj común es el <b>trabajo</b> (aristas revisadas): en cada cuadro "
                    "los dos llevan, como mucho, la misma cantidad. Por eso BFS termina casi de inmediato.</span>",
                    unsafe_allow_html=True)


def explorar():
    encabezado("Explorar", "paso a paso", "Un algoritmo, paso por paso, con su pseudocódigo en vivo.")
    alg = st.segmented_control("Algoritmo", ["bfs", "bellman_ford", "edmonds_karp"], default="bfs",
                               format_func=NOMBRE.get, key="alg-explorar") or "bfs"
    if alg == "edmonds_karp":
        c1, c2 = st.columns(2)
        o = c1.selectbox("Desde la zona", ZONAS, index=0)
        d = c2.selectbox("Hasta la zona", [z for z in ZONAS if z != o], index=len(ZONAS) - 2)
        clave = ("ek", o, d)
        if clave not in ss.videos:
            pasos = []
            _, _, cuellos, _ = ek.entre_zonas(grafo.capacidades(aristas), nodos, o, d, pasos)
            ss.videos[clave] = interactivo.explorar_flujo(nodos, aristas, interactivo.estados_flujo(pasos, cuellos))
        st.plotly_chart(ss.videos[clave], use_container_width=True, key="video-ek", config={"displayModeBar": False})
        st.markdown("<span class='kf-nota'>Edmonds-Karp no busca una ruta entre dos puntos: mide cuántos operarios "
                    "por minuto caben de una zona a otra (capacidad por pasillo: baja 3, media 2, alta 1).</span>",
                    unsafe_allow_html=True)
        return
    with st.expander(f"Puntos: inicio {ss.inicio} · {len(ss.destinos)} destinos · hora {ss.perfil} (cambiar)"):
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
    st.plotly_chart(ss.videos[clave], use_container_width=True, key="video-explorar", config={"displayModeBar": False})


def simular():
    encabezado("Simulación", "de un turno",
               "Varios operarios a la vez: los pasillos más cruzados se congestionan, baja su capacidad y "
               "Edmonds-Karp encuentra dónde se atasca el almacén.")
    c1, c2, c3, c4 = st.columns(4)
    ruta_ops = c1.segmented_control("Los operarios usan", ["bfs", "bellman_ford"], default="bfs",
                                    format_func=NOMBRE.get) or "bfs"
    n_ops = c2.slider("Operarios", 5, 15 if ruta_ops == "bellman_ford" else 60, 10 if ruta_ops == "bellman_ford" else 30)
    max_prod = c3.slider("Productos máx. por pedido", 1, 5, 3)
    hora = c4.segmented_control("Hora", ["punta", "valle"], default="punta", key="hora-sim") or "punta"
    c5, c6, c7, c8 = st.columns([3, 3, 1.5, 1.5])
    z_origen = c5.selectbox("Flujo desde", ZONAS, index=0)
    z_destino = c6.selectbox("hasta", [z for z in ZONAS if z != z_origen], index=len(ZONAS) - 2)
    semilla = c7.number_input("Semilla", 0, 9999, 1)
    c8.write("")
    if c8.button("Simular turno", type="primary", use_container_width=True):
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
    if not ss.turno:
        st.info("Ajusta los parámetros y presiona Simular turno.")
        return
    tr = ss.turno
    res = tr["res"]
    base_valor = flujo_dataset(tr["origen"], tr["destino"])[0]
    c = st.columns(4)
    with c[0]:
        tarjeta("Operarios", len(tr["ops"]), "un pedido cada uno")
    with c[1]:
        tarjeta("Pasillos usados", len(res["uso"]), f"de {len(aristas)}")
    with c[2]:
        tarjeta("Pasillo más cruzado", max(res["uso"].values()), "veces en el turno")
    with c[3]:
        tarjeta("Flujo máximo", res["valor"], f"operarios/min · con la congestión del dataset: {base_valor}")
    st.markdown("### El turno")
    st.plotly_chart(tr["video_turno"], use_container_width=True, key="video-turno", config={"displayModeBar": False})
    st.markdown(f"### Edmonds-Karp *{tr['origen']} → {tr['destino']}*")
    st.plotly_chart(tr["video_flujo"], use_container_width=True, key="video-flujo", config={"displayModeBar": False})


def resultados():
    encabezado("Resultados", "del experimento", "360 pedidos: BFS contra Bellman-Ford en hora valle y punta.")
    resumen = (RAIZ / "resultados" / "resumen.md").read_text(encoding="utf-8")
    st.markdown("\n".join(l for l in resumen.splitlines() if not l.startswith("![") and not l.startswith("# ")))
    c1, c2 = st.columns(2)
    c1.image(str(RAIZ / "resultados" / "ruta_ejemplo.png"))
    c2.image(str(RAIZ / "resultados" / "cuellos_de_botella.png"))


def verificar():
    encabezado("Resultados de", "la verificación",
               "Nuestros algoritmos contra NetworkX, la librería de grafos de referencia: la evidencia detrás "
               "de las cifras del informe.")
    v = json.loads((RAIZ / "resultados" / "verificacion.json").read_text(encoding="utf-8"))
    c = st.columns(4)
    for col, (alg, d) in zip(c, v["algoritmos"].items()):
        with col:
            tarjeta(NOMBRE[alg], d["aciertos"], d["criterio"], f" / {d['consultas']}")
    with c[3]:
        tarjeta("Verificado el", v["fecha"], f"Python {v['python']} · NetworkX {v['networkx']} · {v['segundos']} s")
    st.write("")
    st.markdown(f"""
| Algoritmo | Consultas | Iguales a NetworkX | Error máximo | Criterio |
|---|---|---|---|---|
""" + "\n".join(f"| {NOMBRE[a]} | {d['consultas']} | {d['aciertos']} | {d['error_max']:.1e} | {d['criterio']} |"
                for a, d in v["algoritmos"].items()) + f"""

<span class='kf-nota'>Sistema: {v['sistema']} · semilla {v['semilla']}. Se reproduce con
`python scripts/verificar.py`. Los tiempos de cálculo de la app son descriptivos: dependen de la PC.</span>
""", unsafe_allow_html=True)
    st.markdown("### Verificar *ahora, en este navegador*")
    st.markdown("<span class='kf-nota'>Vuelve a correr una muestra más chica aquí mismo (en tu PC, con otra semilla).</span>",
                unsafe_allow_html=True)
    if st.button("Verificar 40 + 20 + 6 consultas", type="primary"):
        barra = st.progress(0.0)
        ss.verif_vivo = verificacion.verificar(nodos, aristas, 40, 10, semilla=random.randrange(10_000),
                                               progreso=lambda p: barra.progress(min(p, 1.0)))
    if ss.verif_vivo:
        vv = ss.verif_vivo
        st.success(" · ".join(f"{NOMBRE[a]} {d['aciertos']}/{d['consultas']}" for a, d in vv["algoritmos"].items())
                   + f" — {vv['segundos']} s en {vv['sistema']}")


def acerca():
    encabezado("Un laboratorio para", "ver pensar a los algoritmos",
               "Trabajo del curso 1ACC0184 Complejidad Algorítmica (UPC, 2026-2). Caso 2: gestión de almacenes "
               "inteligentes (Amazon). Todo se calcula en Python; esta página corre dentro de tu navegador.")
    algs = [("bfs", "No considera pesos", "Recorridos y búsquedas en grafos", "Cormen et al. (2022)",
             "Ruta con menos pasillos; línea base."),
            ("bellman_ford", "Óptimo con pesos", "Bellman-Ford", "Bellman (1958)",
             "Ruta de menor tiempo con la congestión de cada pasillo."),
            ("edmonds_karp", "Óptimo (flujo)", "Flujo máximo en redes (Ford-Fulkerson)", "Edmonds y Karp (1972)",
             "Capacidad entre zonas y corte mínimo (cuellos de botella).")]
    for col, (a, opt, tec, ref, para) in zip(st.columns(3), algs):
        col.markdown(f"""<div class='kf-card' style='border-top:4px solid {paleta.ALGORITMO[a]}'>
<h3 style='margin:0'>{NOMBRE[a]}</h3><span class='kf-chip'>{opt}</span>
<p class='kf-nota' style='margin-top:10px'>{para}</p>
<div class='kf-etq'>Técnica del enunciado</div><div>{tec}</div>
<div class='kf-etq' style='margin-top:8px'>Complejidad</div><div style='font-family:{paleta.MONO}'>
{COMPLEJIDAD[a][0]} tiempo · {COMPLEJIDAD[a][1]} espacio</div>
<div class='kf-etq' style='margin-top:8px'>Referencia</div><div>{ref}</div></div>""", unsafe_allow_html=True)
    st.markdown(f"""
### Datos

Cuadrícula sintética de 45 × 40 ubicaciones (1 800 nodos, 3 515 pasillos) inspirada en los almacenes robóticos
Kiva (Wurman et al., 2008): Amazon no publica sus planos y los datasets públicos de *order picking* no traen
topología. La congestión de cada pasillo se **mide** simulando 2 000 pedidos (popularidad Zipf o pedidos reales
de *Instacart Market Basket Analysis*, Kaggle) y partiendo los pasillos en tercios.

### Reglas del modelo

Cada ubicación es un vértice; cada pasillo une dos vecinas (4 direcciones) y mide 1,2 m. En hora punta un
pasillo de congestión media pesa ×1,25 y uno alta ×1,6 (en valle ×1,1 y ×1,25). Para el flujo, cada pasillo deja
pasar 3, 2 o 1 operarios por minuto según su congestión. El orden de visita de varios destinos es el del vecino
más cercano (heurística voraz): el óptimo sería el problema del viajero, que es NP-difícil.

### Uso de IA

El código se escribió con asistencia de Claude (Anthropic) y el grupo lo revisó y lo verificó (ver
*Verificación*); está declarado en la bitácora del informe. Código: [{REPO}]({REPO}).
""")


PAGINAS = {
    "inicio": st.Page(inicio, title="Inicio", icon=":material/home:", default=True),
    "explorar": st.Page(explorar, title="Explorar", icon=":material/explore:"),
    "comparar": st.Page(comparar, title="Comparar", icon=":material/compare:"),
    "simular": st.Page(simular, title="Simulación", icon=":material/groups:"),
    "resultados": st.Page(resultados, title="Resultados", icon=":material/bar_chart:"),
    "verificar": st.Page(verificar, title="Verificación", icon=":material/verified:"),
    "acerca": st.Page(acerca, title="Acerca", icon=":material/info:"),
}
nav = st.navigation(list(PAGINAS.values()), position="hidden")
with st.sidebar:
    st.markdown("<div class='kf-marca'>Kiva<em>Flow</em></div>"
                f"<div class='kf-nota'>Laboratorio de rutas · {'demanda Instacart' if fuente == 'instacart' else 'demanda sintética'}</div>",
                unsafe_allow_html=True)
    for seccion, claves in (("Laboratorio", ("inicio", "explorar", "comparar", "simular")),
                            ("Más", ("resultados", "verificar", "acerca"))):
        st.markdown(f"<div class='kf-seccion'>{seccion}</div>", unsafe_allow_html=True)
        for k in claves:
            st.page_link(PAGINAS[k])
    st.markdown(f"<div class='kf-card' style='margin-top:24px;padding:10px 12px'><span style='color:"
                f"{paleta.ALGORITMO['bellman_ford']}'>●</span> <b style='font-size:13px'>Motor en "
                f"{'tu navegador' if EN_NAVEGADOR else 'Python local'}</b><div class='kf-nota'>"
                f"{'Pyodide · sin servidor' if EN_NAVEGADOR else 'streamlit run app.py'}</div></div>",
                unsafe_allow_html=True)
nav.run()
