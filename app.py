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

import random  # noqa: E402
import time  # noqa: E402
import tracemalloc  # noqa: E402
from collections import Counter  # noqa: E402
from pathlib import Path  # noqa: E402

import streamlit as st  # noqa: E402

from kivaflow import config, edmonds_karp as ek, grafo, interactivo, pedido, simulacion  # noqa: E402

RAIZ = Path(__file__).resolve().parent
REPO = "https://github.com/YhoshuaCZ/kivaflow"
ZONAS = [z for z, _ in config.ZONAS]
NOMBRE = {"bfs": "BFS", "bellman_ford": "Bellman-Ford"}
COMPLEJIDAD = {"bfs": ("O(V + E)", "O(V)"), "bellman_ford": ("O(V · E)", "O(V)")}

st.set_page_config(page_title="KivaFlow", page_icon="📦", layout="wide")
ss = st.session_state


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


def medir_memoria(funcion):
    """Memoria pico (KB) que reservó una llamada, medida con tracemalloc."""
    try:
        tracemalloc.start()
        funcion()
        _, pico = tracemalloc.get_traced_memory()
        return round(pico / 1024)
    except Exception:  # noqa: BLE001 (por si el entorno no lo soporta)
        return None
    finally:
        if tracemalloc.is_tracing():
            tracemalloc.stop()


nodos, aristas, popularidad, fuente = datos()
IDS = list(nodos)
por_par = {frozenset((a["Nodo_Origen"], a["Nodo_Destino"])): a for a in aristas}
for clave, valor in {"inicio": None, "destinos": [], "sel_k": 0, "video_ruta": None, "turno": None}.items():
    ss.setdefault(clave, valor)

st.title("📦 KivaFlow")
st.caption("Rutas de picking y cuellos de botella en un almacén tipo Amazon modelado como grafo · "
           f"Complejidad Algorítmica (UPC, 2026-2) · [código en GitHub]({REPO})")

t_rutas, t_sim, t_almacen, t_result, t_acerca = st.tabs(
    ["🧭 Rutas", "🎬 Simulación de un turno", "🏬 Almacén", "📊 Resultados", "ℹ️ Cómo se usa"])

# ======================= RUTAS =======================
with t_rutas:
    st.markdown("**1.** Haz clic en el mapa para marcar el **inicio** y los **destinos** (o usa *Al azar*). "
                "**2.** Elige los algoritmos. **3.** Compara sus rutas y su costo y mira **cómo buscan** en el video.")
    c1, c2, c3, c4 = st.columns([2, 2, 2, 3])
    modo = c1.radio("El clic marca", ["Inicio", "Destino"], horizontal=True,
                    help="Un destino ya marcado se quita con otro clic.")
    perfil = c2.radio("Hora", ["punta", "valle"], horizontal=True,
                      help="En hora punta los pasillos concurridos se frenan más (pesa en Bellman-Ford).")
    regresar = c3.toggle("Volver al inicio", value=False)
    algoritmos = c4.multiselect("Algoritmos", ["bfs", "bellman_ford"], default=["bfs", "bellman_ford"],
                                format_func=NOMBRE.get)
    b1, b2, b3, _ = st.columns([2, 2, 1, 4])
    n_azar = b2.number_input("Destinos al azar", 1, 10, 3, label_visibility="collapsed")
    if b1.button("🎲 Al azar", use_container_width=True):
        rng = random.Random()
        ss.inicio = rng.choice(IDS)
        ss.destinos = rng.sample([n for n in IDS if n != ss.inicio], n_azar)
        ss.video_ruta = None
    if b3.button("🧹", help="Limpiar puntos"):
        ss.inicio, ss.destinos, ss.video_ruta = None, [], None

    # --- calcular rutas ---
    ady, dirigidas = estructuras(perfil)
    rutas, filas = {}, []
    if ss.inicio and ss.destinos:
        for alg in algoritmos:
            t0 = time.perf_counter()
            r = pedido.ruta_pedido(ady, dirigidas, ss.inicio, ss.destinos, alg, regresar=regresar)
            ms = (time.perf_counter() - t0) * 1000
            kb = medir_memoria(lambda a=alg: pedido.ruta_pedido(ady, dirigidas, ss.inicio, ss.destinos, a,
                                                                regresar=regresar))
            m = pedido.medir(r["camino"], por_par, perfil)
            rutas[alg] = r["camino"]
            filas.append({"Algoritmo": NOMBRE[alg], "Tiempo caminando (s)": m["tiempo_s"],
                          "Pasillos": m["pasillos"], "Metros": m["distancia_m"],
                          "Cálculo (ms)": round(ms, 1), "Nodos visitados": r["nodos_visitados"],
                          "Relajaciones": r["relajaciones"] if alg == "bellman_ford" else None,
                          "Memoria pico (KB)": kb,
                          "Tiempo O()": COMPLEJIDAD[alg][0], "Espacio O()": COMPLEJIDAD[alg][1],
                          "Orden de visita": " → ".join(r["orden"])})

    # --- mapa clicable ---
    fig = interactivo.mapa(nodos, aristas, ss.inicio, ss.destinos, rutas)
    evento = st.plotly_chart(fig, key=f"mapa{ss.sel_k}", on_select="rerun", selection_mode="points",
                             use_container_width=True, config={"scrollZoom": True})
    puntos = [p for p in (evento.selection.points if evento else []) if p.get("curve_number") == interactivo.NODOS_TRAZA]
    if puntos:
        nodo = IDS[puntos[0]["point_index"]]
        if modo == "Inicio":
            ss.inicio = nodo
        elif nodo in ss.destinos:
            ss.destinos.remove(nodo)
        elif len(ss.destinos) < 10 and nodo != ss.inicio:
            ss.destinos.append(nodo)
        ss.sel_k += 1          # reinicia la selección del gráfico para el próximo clic
        ss.video_ruta = None
        st.rerun()

    st.markdown(f"**Inicio:** `{ss.inicio or '—'}` · **Destinos:** "
                + (", ".join(f"`{d}`" for d in ss.destinos) or "—"))
    if filas:
        st.dataframe(filas, hide_index=True, use_container_width=True)
        if len(filas) == 2:
            a, b = filas
            ahorro = a["Tiempo caminando (s)"] - b["Tiempo caminando (s)"]
            veces = b["Cálculo (ms)"] / max(a["Cálculo (ms)"], 0.1)
            st.markdown(f"Bellman-Ford **ahorra {ahorro:.1f} s** de caminata frente a BFS, pero su cálculo cuesta "
                        f"**{veces:.0f} veces** más. Ese es el trade-off: mejor ruta contra más procesamiento."
                        if ahorro > 0.05 else
                        "Aquí las dos rutas cuestan lo mismo (los pasillos del camino corto no estaban congestionados), "
                        f"pero Bellman-Ford calculó **{veces:.0f} veces** más.")

        st.subheader("🎬 Cómo busca cada algoritmo")
        v1, v2 = st.columns([2, 5])
        alg_video = v1.radio("Ver", algoritmos, format_func=NOMBRE.get, key="alg_video")
        if v1.button("Preparar video", type="primary"):
            registro = []
            pedido.ruta_pedido(ady, dirigidas, ss.inicio, ss.destinos, alg_video, registro, regresar=regresar)
            ss.video_ruta = interactivo.animacion_busqueda(nodos, aristas, registro, alg_video, ss.inicio, ss.destinos)
        v2.markdown("- **BFS** se expande en **anillos** (niveles): todos los nodos a 1 pasillo, luego a 2… "
                    "y para en el primer destino que toca.\n"
                    "- **Bellman-Ford** avanza por **rondas**: en cada una revisa todas las aristas y mejora las "
                    "distancias (en naranja, lo que mejoró en esa ronda). No puede parar antes de converger.\n"
                    "- Usa ▶ x0.5 … x4 para la velocidad, ⏸ para pausar y la barra para adelantar o retroceder.")
        if ss.video_ruta is not None:
            st.plotly_chart(ss.video_ruta, use_container_width=True, key="video_ruta_chart")
    else:
        st.info("Marca un inicio y al menos un destino para ver las rutas.")
    st.caption("Edmonds-Karp no busca una ruta entre dos puntos: mide **cuántos operarios caben** entre dos zonas. "
               "Está en la pestaña *Simulación de un turno*.")

# ======================= SIMULACIÓN =======================
with t_sim:
    st.markdown("Simula **un turno**: varios operarios hacen pedidos a la vez. Los pasillos más cruzados se "
                "**congestionan**, eso baja su capacidad y **Edmonds-Karp** encuentra cuántos operarios por minuto "
                "pueden ir de una zona a otra y **dónde se atascan**.")
    c1, c2, c3, c4 = st.columns(4)
    ruta_ops = c1.radio("Los operarios usan", ["bfs", "bellman_ford"], format_func=NOMBRE.get, horizontal=True,
                        help="Bellman-Ford es más lento de calcular en el navegador: máximo 15 operarios.")
    n_ops = c2.slider("Operarios", 5, 15 if ruta_ops == "bellman_ford" else 60, 10 if ruta_ops == "bellman_ford" else 30)
    max_prod = c3.slider("Productos máx. por pedido", 1, 5, 3)
    hora = c4.radio("Hora ", ["punta", "valle"], horizontal=True)
    c5, c6, c7 = st.columns([3, 3, 2])
    z_origen = c5.selectbox("Flujo desde", ZONAS, index=0)
    z_destino = c6.selectbox("hasta", [z for z in ZONAS if z != z_origen], index=len(ZONAS) - 2)
    semilla = c7.number_input("Semilla", 0, 9999, 1)
    if st.button("▶ Simular turno", type="primary"):
        with st.spinner("Calculando rutas, congestión y flujo máximo…"):
            ady_s, dir_s = estructuras(hora)
            ops = simulacion.turno(nodos, ady_s, dir_s, popularidad, n_ops, max_prod, ruta_ops, semilla)
            pasos = []
            res = simulacion.congestion_y_flujo(nodos, aristas, ops, z_origen, z_destino, pasos)
            ss.turno = {
                "ops": ops, "res": res, "origen": z_origen, "destino": z_destino,
                "video_turno": interactivo.animacion_turno(nodos, aristas, ops),
                "video_flujo": interactivo.animacion_flujo(
                    nodos, aristas, pasos, res["cuellos"], res["stats"]["lado_fuente"], res["niveles"],
                    f"Edmonds-Karp con la congestión del turno: dale ▶"),
            }

    if ss.turno:
        tr = ss.turno
        res = tr["res"]
        base_valor = flujo_dataset(tr["origen"], tr["destino"])[0]
        niv = Counter(res["niveles"][(u, v)] if (u, v) in res["niveles"] else res["niveles"][(v, u)]
                      for u, v, _ in res["cuellos"])
        c = st.columns(4)
        c[0].metric("Operarios", len(tr["ops"]))
        c[1].metric("Pasillos usados", f"{len(res['uso'])} / {len(aristas)}")
        c[2].metric("Pasillo más cruzado", f"{max(res['uso'].values())} veces")
        c[3].metric("Flujo máximo del turno", f"{res['valor']} op/min",
                    delta=f"{res['valor'] - base_valor:+} vs. congestión del dataset ({base_valor})")

        st.subheader("1 · El turno: operarios moviéndose y pasillos calentándose")
        st.plotly_chart(tr["video_turno"], use_container_width=True, key="video_turno_chart")
        st.subheader(f"2 · Edmonds-Karp: {tr['origen']} → {tr['destino']}")
        suma = " + ".join(f"{niv[n]}·{config.CAPACIDAD_OPERARIOS_MIN[n]}" for n in ("Alta", "Media", "Baja") if niv[n])
        st.markdown(f"Cada cuadro es un **camino de aumento** encontrado con BFS. Cuando ya no hay más, los pasillos "
                    f"saturados forman el **corte mínimo**: {suma} = **{res['valor']}** = flujo máximo.")
        st.plotly_chart(tr["video_flujo"], use_container_width=True, key="video_flujo_chart")
    else:
        st.info("Ajusta los parámetros y presiona **▶ Simular turno**.")

# ======================= ALMACÉN =======================
with t_almacen:
    niveles = Counter(a["Frecuencia_Pedidos"] for a in aristas)
    c = st.columns(4)
    c[0].metric("Nodos (ubicaciones)", len(nodos))
    c[1].metric("Aristas (pasillos)", len(aristas))
    c[2].metric("Racks / muelles", f"{sum(n['Tipo'] == 'rack' for n in nodos.values())} / "
                                   f"{sum(n['Tipo'] == 'estacion' for n in nodos.values())}")
    c[3].metric("Demanda", "Instacart" if fuente == "instacart" else "Sintética",
                help="Instacart = pedidos reales de Kaggle; sintética = popularidad Zipf.")
    st.markdown(
        f"Cuadrícula de {config.FILAS} × {config.COLUMNAS} con {config.CELDA_M} m entre ubicaciones, en tres zonas "
        f"por columnas. La congestión de cada pasillo se **midió** simulando {config.N_PEDIDOS} pedidos y partiendo "
        f"los pasillos en tercios según cuántas veces se cruzaron: Baja {niveles['Baja']}, Media {niveles['Media']}, "
        f"Alta {niveles['Alta']}. Pasa el mouse por un punto para ver su id, zona y SKU.")
    fig_alm = interactivo.base(nodos, aristas, suave=False)
    fig_alm.update_layout(title=f"Almacén: {len(nodos)} nodos, {len(aristas)} aristas")
    st.plotly_chart(fig_alm, use_container_width=True, key="almacen_chart")

# ======================= RESULTADOS =======================
with t_result:
    resumen = (RAIZ / "resultados" / "resumen.md").read_text(encoding="utf-8")
    st.markdown("\n".join(l for l in resumen.splitlines() if not l.startswith("![")))
    c1, c2 = st.columns(2)
    c1.image(str(RAIZ / "resultados" / "ruta_ejemplo.png"))
    c2.image(str(RAIZ / "resultados" / "cuellos_de_botella.png"))

# ======================= CÓMO SE USA =======================
with t_acerca:
    st.markdown(f"""
**Rutas.** Clic en el mapa para marcar el inicio y los destinos (o *Al azar*). La app calcula la ruta con BFS y
con Bellman-Ford (visitando los destinos en orden de vecino más cercano) y compara tiempo caminando, cálculo,
nodos visitados y memoria. *Preparar video* reproduce la búsqueda paso a paso.

**Simulación de un turno.** Varios operarios trabajan a la vez → se cuentan los cruces por pasillo → congestión
Baja/Media/Alta (por tercios) → capacidad de cada pasillo (3/2/1 operarios por minuto) → Edmonds-Karp da el flujo
máximo entre dos zonas y el corte mínimo (los cuellos de botella).

| Algoritmo | Para qué | Tiempo | Espacio |
|---|---|---|---|
| BFS | Ruta con menos pasillos (línea base) | O(V + E) | O(V) |
| Bellman-Ford | Ruta de menor tiempo con congestión | O(V · E) | O(V) |
| Edmonds-Karp | Flujo máximo y cuellos de botella | O(V · E²) | O(V + E) |
| Vecino más cercano | Orden de visita de los destinos (el óptimo sería el TSP, NP-difícil) | k + 1 búsquedas | — |

Los algoritmos están programados a mano y verificados contra NetworkX en los tests. Las animaciones usan los
pasos que anotan los propios algoritmos. Código: [{REPO}]({REPO}).

La app corre **dentro de tu navegador** con [stlite](https://github.com/whitphx/stlite): no hay servidor, por eso
la primera carga tarda unos segundos y los cálculos dependen de tu PC.
""")
