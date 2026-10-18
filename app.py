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
from collections import Counter  # noqa: E402
from pathlib import Path  # noqa: E402

import streamlit as st  # noqa: E402

from kivaflow import config, edmonds_karp as ek, grafo, pedido, visual  # noqa: E402

RAIZ = Path(__file__).resolve().parent
REPO = "https://github.com/YhoshuaCZ/kivaflow"
ZONAS = [z for z, _ in config.ZONAS]

st.set_page_config(page_title="KivaFlow", page_icon="📦", layout="wide")


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
def figura_almacen():
    nodos, aristas, _, _ = datos()
    return visual.almacen(nodos, aristas, tamano=(10, 11))


@st.cache_resource
def flujo(origen, destino):
    nodos, aristas, _, _ = datos()
    return ek.entre_zonas(grafo.capacidades(aristas), nodos, origen, destino)


nodos, aristas, popularidad, fuente = datos()
por_par = {frozenset((a["Nodo_Origen"], a["Nodo_Destino"])): a for a in aristas}

st.title("📦 KivaFlow")
st.caption("Rutas de picking y cuellos de botella en un almacén tipo Amazon modelado como grafo · "
           f"Complejidad Algorítmica (UPC, 2026-2) · [código en GitHub]({REPO})")

t_almacen, t_ruta, t_flujo, t_result, t_acerca = st.tabs(
    ["🏬 Almacén", "🧭 Ruta de picking", "🚧 Cuellos de botella", "📊 Resultados", "ℹ️ Acerca de"])

# ---------- Almacén ----------
with t_almacen:
    niveles = Counter(a["Frecuencia_Pedidos"] for a in aristas)
    c = st.columns(4)
    c[0].metric("Nodos (ubicaciones)", len(nodos))
    c[1].metric("Aristas (pasillos)", len(aristas))
    c[2].metric("Racks / muelles", f"{sum(n['Tipo'] == 'rack' for n in nodos.values())} / "
                                   f"{sum(n['Tipo'] == 'estacion' for n in nodos.values())}")
    c[3].metric("Demanda", "Instacart" if fuente == "instacart" else "Sintética", help="Instacart = pedidos reales de Kaggle; sintética = popularidad Zipf.")
    st.markdown(
        f"Cuadrícula de {config.FILAS} × {config.COLUMNAS} con {config.CELDA_M} m entre ubicaciones, "
        "en tres zonas por columnas. La congestión de cada pasillo se **midió** simulando "
        f"{config.N_PEDIDOS} pedidos: Baja {niveles['Baja']}, Media {niveles['Media']}, Alta {niveles['Alta']} pasillos.")
    st.pyplot(figura_almacen(), width="content")

# ---------- Ruta de picking ----------
with t_ruta:
    st.markdown("Arma un pedido y compara la ruta de **BFS** (menos pasillos, ignora la congestión) "
                "con la de **Bellman-Ford** (menor tiempo según la congestión). En ambas, el orden de visita "
                "es el del **vecino más cercano** (heurística voraz).")
    c1, c2, c3 = st.columns(3)
    perfil = c1.radio("Hora", ["punta", "valle"], horizontal=True,
                      help="En hora punta los pasillos concurridos se frenan más.")
    k = c2.slider("Productos en el pedido", 1, 10, 5)
    semilla = c3.number_input("Pedido aleatorio n.º", 0, 9999, 0, help="Cambia el número para otro pedido.")

    muelle, racks = pedido.aleatorio(nodos, popularidad, k, random.Random(semilla))
    ady, dirigidas = estructuras(perfil)
    resultados = {}
    for e in ("bfs", "bellman_ford"):
        r = pedido.ruta_pedido(ady, dirigidas, muelle, racks, e)
        resultados[e] = (r, pedido.medir(r["camino"], por_par, perfil))

    (rb, mb), (rf, mf) = resultados["bfs"], resultados["bellman_ford"]
    c = st.columns(4)
    c[0].metric("Tiempo BFS", f"{mb['tiempo_s']} s")
    c[1].metric("Tiempo Bellman-Ford", f"{mf['tiempo_s']} s",
                delta=f"{mf['tiempo_s'] - mb['tiempo_s']:.1f} s", delta_color="inverse")
    c[2].metric("Pasillos BFS / B-F", f"{mb['pasillos']} / {mf['pasillos']}")
    c[3].metric("Cálculo BFS / B-F", f"{rb['segundos'] * 1000:.0f} / {rf['segundos'] * 1000:.0f} ms")

    izq, der = st.columns([3, 2])
    with izq:
        caminos = {
            f"BFS: {mb['pasillos']} pasillos, {mb['tiempo_s']} s": (rb["camino"], "#2b6cb0", 4),
            f"Bellman-Ford: {mf['pasillos']} pasillos, {mf['tiempo_s']} s": (rf["camino"], "#2f855a", 2),
        }
        st.pyplot(visual.rutas(nodos, aristas, caminos, racks, muelle,
                               f"Pedido n.º {semilla}: {k} productos, hora {perfil}", tamano=(8, 9)),
                  width="content")
    with der:
        st.markdown(f"**Sale de** el muelle `{muelle}` y vuelve a él.")
        st.dataframe([{"Rack": n, "SKU": nodos[n]["SKU"], "Zona": nodos[n]["Zona"],
                       "Veces pedido": popularidad.get(nodos[n]["SKU"], 0)} for n in racks],
                     hide_index=True)
        st.markdown("**Orden de visita**")
        st.markdown(f"- BFS: {' → '.join(rb['orden'])}\n- Bellman-Ford: {' → '.join(rf['orden'])}")
        st.dataframe([
            {"Algoritmo": "BFS", "Pasillos": mb["pasillos"], "Metros": mb["distancia_m"],
             "Metros ajustados": mb["distancia_ajustada_m"], "Nodos visitados": rb["nodos_visitados"],
             "Relajaciones": None},
            {"Algoritmo": "Bellman-Ford", "Pasillos": mf["pasillos"], "Metros": mf["distancia_m"],
             "Metros ajustados": mf["distancia_ajustada_m"], "Nodos visitados": rf["nodos_visitados"],
             "Relajaciones": rf["relajaciones"]},
        ], hide_index=True)

# ---------- Cuellos de botella ----------
with t_flujo:
    st.markdown("**Edmonds-Karp** calcula cuántos operarios por minuto pueden ir de una zona a otra "
                "(capacidad por pasillo: Baja 3, Media 2, Alta 1) y el **corte mínimo**: los pasillos saturados "
                "que ponen el límite.")
    c1, c2 = st.columns(2)
    origen = c1.selectbox("Desde la zona", ZONAS, index=0)
    destino = c2.selectbox("Hasta la zona", [z for z in ZONAS if z != origen], index=len(ZONAS) - 2)
    valor, _, cuellos, stats = flujo(origen, destino)
    niv = Counter(por_par[frozenset((u, v))]["Frecuencia_Pedidos"] for u, v, _ in cuellos)
    c = st.columns(3)
    c[0].metric("Flujo máximo", f"{valor} operarios/min")
    c[1].metric("Pasillos en el corte", len(cuellos))
    c[2].metric("Caminos de aumento (BFS)", stats["caminos_aumento"])
    suma = " + ".join(f"{niv[n]}·{config.CAPACIDAD_OPERARIOS_MIN[n]}" for n in ("Alta", "Media", "Baja") if niv[n])
    st.markdown(f"Comprobación (flujo máximo = corte mínimo): {suma} = **{valor}** "
                f"(Alta · 1, Media · 2, Baja · 3).")
    st.pyplot(visual.corte(nodos, aristas, cuellos, stats["lado_fuente"],
                           f"{origen} → {destino}: {valor} operarios/min", tamano=(8, 9)),
              width="content")

# ---------- Resultados ----------
with t_result:
    resumen = (RAIZ / "resultados" / "resumen.md").read_text(encoding="utf-8")
    st.markdown("\n".join(l for l in resumen.splitlines() if not l.startswith("![")))
    c1, c2 = st.columns(2)
    c1.image(str(RAIZ / "resultados" / "ruta_ejemplo.png"))
    c2.image(str(RAIZ / "resultados" / "cuellos_de_botella.png"))

# ---------- Acerca de ----------
with t_acerca:
    st.markdown(f"""
| Algoritmo | Para qué | Complejidad |
|---|---|---|
| BFS | Ruta con menos pasillos (línea base) | O(V + E) |
| Bellman-Ford | Ruta de menor tiempo con congestión | O(V · E) |
| Edmonds-Karp | Flujo máximo y cuellos de botella | O(V · E²) |
| Vecino más cercano | Orden de visita de un pedido (TSP es NP-difícil) | k + 1 búsquedas |

Los tres algoritmos están programados a mano y verificados contra NetworkX en los tests.
Código, dataset y documentación: [{REPO}]({REPO}).

Esta app corre **dentro de tu navegador** con [stlite](https://github.com/whitphx/stlite) (Python compilado
a WebAssembly): no hay servidor. Por eso la primera carga tarda unos segundos.
""")
