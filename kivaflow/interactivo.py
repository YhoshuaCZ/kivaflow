"""Figuras interactivas (Plotly) para la app: mapa clicable y animaciones tipo video.

Las animaciones se arman con los PASOS que anotan los propios algoritmos
(`pasos=` en bfs, bellman_ford y edmonds_karp): lo que se ve es lo que hizo el
algoritmo, no una imitación. Plotly reproduce los cuadros en el navegador
(play, pausa, velocidad y barra para adelantar o retroceder) sin volver a calcular.
"""
import math

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from . import bellman_ford as bf
from . import paleta, simulacion
from .bfs import reconstruir

ALTO = 640
NOMBRE = {"bfs": "BFS", "bellman_ford": "Bellman-Ford", "edmonds_karp": "Edmonds-Karp"}
NODOS_TRAZA = 3  # índice de la traza de nodos (la que se puede cliquear) en `mapa`
NBSP = " "

PSEUDO = {
    "bfs": [
        "visto = {inicio}; cola = [inicio]",
        "mientras la cola no esté vacía:",
        "    u = sacar el primero de la cola",
        "    si u es un destino: devolver la ruta",
        "    para cada vecino v de u:",
        "        si v no está en visto:",
        "            visto += v; padre[v] = u",
        "            meter v al final de la cola",
        "devolver SIN_RUTA",
    ],
    "bellman_ford": [
        "dist[*] = ∞; dist[inicio] = 0",
        "repetir (como máximo V − 1 rondas):",
        "    cambio = falso",
        "    para cada arista (u, v, w):",
        "        si dist[u] + w < dist[v]:",
        "            dist[v] = dist[u] + w; padre[v] = u",
        "            cambio = verdadero",
        "    si no hubo cambio: terminar",
        "si una ronda extra mejora: ciclo negativo",
        "devolver dist, padre",
    ],
    "edmonds_karp": [
        "flujo = 0; residual = capacidades",
        "mientras BFS halle un camino s → t:",
        "    δ = capacidad mínima del camino",
        "    en cada arista (u, v) del camino:",
        "        residual[u][v] −= δ",
        "        residual[v][u] += δ",
        "    flujo += δ",
        "corte = alcanzables desde s en residual",
        "devolver flujo, corte",
    ],
}


# ---------- utilidades ----------

def _pos(nodos):
    return {k: (float(n["X_m"]), -float(n["Y_m"])) for k, n in nodos.items()}


def _xy(pos, ids):
    ids = list(ids)
    return [pos[i][0] for i in ids], [pos[i][1] for i in ids]


def _segmentos(pos, pares):
    xs, ys = [], []
    for u, v in pares:
        xs += [pos[u][0], pos[v][0], None]
        ys += [pos[u][1], pos[v][1], None]
    return xs, ys


def _miles(n):
    return f"{n:,.0f}".replace(",", " ")


def _agrupar(n, maximo):
    """Índices de corte para mostrar n pasos en a lo sumo `maximo` cuadros."""
    if n <= maximo:
        return list(range(n))
    paso = math.ceil(n / maximo)
    return list(range(paso - 1, n, paso)) + ([n - 1] if (n - 1) % paso else [])


def _estilo(fig, titulo="", alto=ALTO):
    fig.update_layout(
        height=alto, margin=dict(l=8, r=8, t=64, b=8), dragmode="pan",
        paper_bgcolor=paleta.TARJETA, plot_bgcolor=paleta.TARJETA,
        font=dict(family=paleta.SANS, color=paleta.TINTA, size=12),
        title=dict(text=titulo, font=dict(family=paleta.SERIF, size=17, color=paleta.TINTA), x=0.01, y=0.97),
        legend=dict(orientation="h", y=-0.02, font=dict(size=11, color=paleta.SUAVE)),
        hoverlabel=dict(bgcolor=paleta.TARJETA, bordercolor=paleta.BORDE, font=dict(family=paleta.SANS)),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False, visible=False)
    fig.update_yaxes(showgrid=False, zeroline=False, showticklabels=False, visible=False)
    return fig


def _trazas_base(nodos, aristas, niveles=None, fuerte=False, opacidad=0.35, mostrar_leyenda=True):
    """3 trazas de pasillos (Baja, Media, Alta) + 1 traza de nodos."""
    pos = _pos(nodos)
    colores = paleta.CONGESTION if fuerte else {"Baja": "#EFEBE3", "Media": "#E8CF9C", "Alta": "#D9A496"}
    trazas = []
    for nivel in ("Baja", "Media", "Alta"):
        pares = [(a["Nodo_Origen"], a["Nodo_Destino"]) for a in aristas
                 if (niveles[(a["Nodo_Origen"], a["Nodo_Destino"])] if niveles else a["Frecuencia_Pedidos"]) == nivel]
        x, y = _segmentos(pos, pares)
        trazas.append(go.Scatter(x=x, y=y, mode="lines", hoverinfo="skip", name=f"Congestión {nivel.lower()}",
                                 showlegend=mostrar_leyenda,
                                 line=dict(color=colores[nivel], width=2.4 if nivel == "Alta" else 1.6)))
    ids = list(nodos)
    x, y = _xy(pos, ids)
    trazas.append(go.Scatter(
        x=x, y=y, mode="markers", name="Ubicaciones", customdata=ids, showlegend=False,
        marker=dict(size=5, color=[paleta.ZONA[nodos[i]["Zona"]] for i in ids], opacity=opacidad,
                    symbol=["square" if nodos[i]["Tipo"] == "estacion" else "circle" for i in ids]),
        text=[f"{i} · {nodos[i]['Zona']} · {nodos[i]['Tipo']}" + (f" · {nodos[i]['SKU']}" if nodos[i]["SKU"] else "")
              for i in ids],
        hovertemplate="%{text}<extra></extra>"))
    return trazas


def _marcadores(pos, inicio, destinos, leyenda=True):
    trazas = []
    if destinos:
        x, y = _xy(pos, destinos)
        trazas.append(go.Scatter(x=x, y=y, mode="markers", name="Destinos", hoverinfo="skip", showlegend=leyenda,
                                 marker=dict(size=13, color=paleta.TARJETA,
                                             line=dict(color=paleta.TINTA, width=2.5))))
    if inicio:
        trazas.append(go.Scatter(x=[pos[inicio][0]], y=[pos[inicio][1]], mode="markers", name="Inicio",
                                 hoverinfo="skip", showlegend=leyenda,
                                 marker=dict(size=14, color=paleta.TINTA, symbol="circle")))
    return trazas


def _controles(fig, nombres, ms=150):
    """Reproductor: ⟲, play x0.5–x4, pausa y barra para moverse por los cuadros."""
    def play(d):
        return [None, {"frame": {"duration": d, "redraw": False}, "fromcurrent": True,
                       "transition": {"duration": 0}, "mode": "immediate"}]

    quieto = {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}
    botones = [dict(label="⟲", method="animate", args=[[nombres[0]], quieto])]
    botones += [dict(label=f"▶ {v:g}×", method="animate", args=play(ms / v)) for v in (0.5, 1, 2, 4)]
    botones.append(dict(label="❚❚", method="animate", args=[[None], quieto]))
    fig.update_layout(
        updatemenus=[dict(type="buttons", direction="left", x=0, y=-0.03, xanchor="left", yanchor="top",
                          showactive=False, bgcolor=paleta.PAPEL, bordercolor=paleta.BORDE,
                          font=dict(color=paleta.TINTA, size=12), pad=dict(r=6, t=4), buttons=botones)],
        sliders=[dict(active=0, x=0.36, len=0.64, y=-0.02, yanchor="top", pad=dict(t=8, b=0),
                      bgcolor=paleta.BORDE, activebgcolor=paleta.TINTA, bordercolor=paleta.BORDE,
                      tickcolor=paleta.TARJETA, font=dict(color=paleta.TARJETA, size=1),
                      currentvalue=dict(prefix="Cuadro ", font=dict(color=paleta.SUAVE, size=11)),
                      steps=[dict(label=str(i + 1), method="animate", args=[[n], quieto])
                             for i, n in enumerate(nombres)])],
        legend=dict(y=-0.13),
        margin=dict(b=90),
    )


# ---------- mapa para elegir puntos ----------

def base(nodos, aristas, niveles=None, suave=True):
    """Figura con el almacén: trazas 0-2 pasillos por congestión, traza 3 nodos (clicables)."""
    fig = go.Figure(_trazas_base(nodos, aristas, niveles, fuerte=not suave))
    _estilo(fig)
    fig.update_yaxes(scaleanchor="x")
    return fig


def mapa(nodos, aristas, inicio=None, destinos=(), rutas=None, titulo="Haz clic en una ubicación"):
    """Mapa para elegir puntos con clic. rutas: {algoritmo: camino} para dibujarlas encima."""
    pos = _pos(nodos)
    fig = base(nodos, aristas)
    for alg, camino in (rutas or {}).items():
        x, y = _xy(pos, camino)
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name=NOMBRE[alg], hoverinfo="skip",
                                 line=dict(color=paleta.ALGORITMO[alg], width=5 if alg == "bfs" else 3)))
    for t in _marcadores(pos, inicio, destinos):
        fig.add_trace(t)
    fig.update_layout(title_text=titulo)
    return fig


# ---------- estados: qué hizo el algoritmo en cada momento ----------

def estados_busqueda(registro, algoritmo, inicio, ady, n_aristas_dirigidas, max_cuadros=150):
    """Convierte el registro de una ruta (una búsqueda por tramo) en estados para animar.

    Cada estado: exp (nodos alcanzados en el tramo), frente (los de este paso), ruta
    (acumulada), linea (1-based en PSEUDO), contadores {linea: n}, texto (narración) y
    trabajo (aristas revisadas desde el inicio: grado de cada nodo sacado en BFS;
    todas las aristas por ronda en Bellman-Ford).
    """
    estados, ruta = [], [inicio]
    trabajo = sacados = rondas = mejoras = 0
    n_tramos = len(registro)
    por_tramo = max(5, max_cuadros // max(1, n_tramos))
    for i, r in enumerate(registro, 1):
        if algoritmo == "bfs":
            grupos = {}
            for u, nivel in r["pasos"]:
                grupos.setdefault(nivel, []).append(u)
            etapas = [grupos[k] for k in sorted(grupos)]
        else:
            etapas = r["pasos"]
        vistos, explorados, acumulados = set(), [], []
        for j, e in enumerate(etapas):
            for n in e:
                if n not in vistos:
                    vistos.add(n)
                    explorados.append(n)
            if algoritmo == "bfs":
                sacados += len(e)
                trabajo += sum(len(ady[n]) for n in e)
                texto = (f"Tramo {i}/{n_tramos} · nivel {j}: salen {len(e)} nodos de la cola "
                         f"({_miles(len(explorados))} alcanzados en el tramo).")
                linea, cont = 3, {3: sacados}
            else:
                rondas += 1
                mejoras += len(e)
                trabajo += n_aristas_dirigidas
                if e:
                    texto = (f"Tramo {i}/{n_tramos} · ronda {j + 1}: mejoraron {_miles(len(e))} distancias "
                             f"({_miles(len(explorados))} nodos alcanzados).")
                    linea = 6
                else:
                    texto = (f"Tramo {i}/{n_tramos} · ronda {j + 1}: nada mejoró, termina sin llegar a "
                             "V − 1 = 1 799 rondas.")
                    linea = 8
                cont = {2: rondas, 6: mejoras}
            acumulados.append(dict(exp=list(explorados), frente=list(e), ruta=list(ruta), linea=linea,
                                   contadores=cont, texto=texto, trabajo=trabajo))
        estados += [acumulados[j] for j in _agrupar(len(acumulados), por_tramo)]
        ruta += r["tramo"][1:]
        fin = r["tramo"][-1]
        texto = (f"Tramo {i}/{n_tramos} listo: llega a {fin} · ruta acumulada de {len(ruta) - 1} pasillos.")
        cont = {3: sacados, 4: i} if algoritmo == "bfs" else {2: rondas, 6: mejoras, 10: i}
        estados.append(dict(exp=[], frente=[], ruta=list(ruta), linea=4 if algoritmo == "bfs" else 10,
                            contadores=cont, texto=texto, trabajo=trabajo))
    return estados


def estados_flujo(pasos, cuellos):
    """Estados de Edmonds-Karp: un camino de aumento por estado y, al final, el corte."""
    estados, usados, total = [], [], 0
    for k, (camino, delta) in enumerate(pasos, 1):
        reales = [n for n in camino if not n.startswith("__")]
        pares = list(zip(reales, reales[1:]))
        usados += pares
        total += delta
        estados.append(dict(usados=list(usados), camino=pares, corte=[], linea=6,
                            contadores={2: k, 6: total},
                            texto=f"Camino de aumento {k}/{len(pasos)}: BFS halló {len(reales) - 1} pasillos "
                                  f"con capacidad libre · +{delta:g} → flujo {total:g} operarios/min."))
    estados.append(dict(usados=list(usados), camino=[], corte=[(u, v) for u, v, _ in cuellos], linea=8,
                        contadores={2: len(pasos), 6: total, 8: 1},
                        texto=f"BFS ya no halla caminos: flujo máximo {total:g} = capacidad del corte "
                              f"mínimo ({len(cuellos)} pasillos saturados)."))
    return estados


# ---------- pseudocódigo ----------

def _codigo(algoritmo, linea, contadores):
    lineas = PSEUDO[algoritmo]
    n = len(lineas)
    ys = [-(i + 1) for i in range(n)]
    textos = [f"{i + 1:>2}{NBSP}{NBSP}" + l.replace(" ", NBSP) for i, l in enumerate(lineas)]
    colores = [paleta.TINTA if i + 1 == linea else paleta.SUAVE for i in range(n)]
    textos = [f"<b>{t}</b>" if i + 1 == linea else t for i, t in enumerate(textos)]
    cont = [f"×{_miles(contadores[i + 1])}" if contadores.get(i + 1) else "" for i in range(n)]
    return ys, textos, colores, cont


def _panel_codigo(fig, algoritmo, estado, col):
    """Trazas del pseudocódigo en la columna `col`: resaltado, texto y contadores."""
    ys, textos, colores, cont = _codigo(algoritmo, estado["linea"], estado["contadores"])
    n = len(textos)
    fig.add_trace(go.Scatter(x=[0, 1], y=[-estado["linea"]] * 2, mode="lines", hoverinfo="skip", showlegend=False,
                             line=dict(color=paleta.ALGORITMO_CLARO[algoritmo], width=22)), row=1, col=col)
    fig.add_trace(go.Scatter(x=[0.01] * n, y=ys, mode="text", text=textos, textposition="middle right",
                             hoverinfo="skip", showlegend=False,
                             textfont=dict(family=paleta.MONO, size=12, color=colores)), row=1, col=col)
    fig.add_trace(go.Scatter(x=[0.99] * n, y=ys, mode="text", text=cont, textposition="middle left",
                             hoverinfo="skip", showlegend=False,
                             textfont=dict(family=paleta.MONO, size=11, color=paleta.ALGORITMO[algoritmo])),
                  row=1, col=col)
    fig.update_xaxes(range=[0, 1], row=1, col=col)
    fig.update_yaxes(range=[-(n + 0.7), 0.3], row=1, col=col)


def _frame_codigo(algoritmo, estado):
    ys, textos, colores, cont = _codigo(algoritmo, estado["linea"], estado["contadores"])
    return [go.Scatter(x=[0, 1], y=[-estado["linea"]] * 2),
            go.Scatter(text=textos, textfont=dict(color=colores)),
            go.Scatter(text=cont)]


# ---------- Explorar: un algoritmo con su pseudocódigo ----------

def _lienzo_con_codigo(titulo):
    fig = make_subplots(rows=1, cols=2, column_widths=[0.6, 0.4], horizontal_spacing=0.02,
                        subplot_titles=["", "Pseudocódigo"])
    _estilo(fig, titulo, alto=620)
    fig.update_yaxes(scaleanchor="x", row=1, col=1)
    for a in fig.layout.annotations:
        if a.text == "Pseudocódigo":
            a.update(font=dict(family=paleta.SERIF, size=14, color=paleta.SUAVE), x=0.62, xanchor="left")
    return fig


def explorar(nodos, aristas, estados, algoritmo, inicio, destinos):
    """Video de BFS o Bellman-Ford con su pseudocódigo iluminado y la narración paso a paso."""
    pos = _pos(nodos)
    fig = _lienzo_con_codigo(estados[0]["texto"])
    for t in _trazas_base(nodos, aristas):
        fig.add_trace(t, row=1, col=1)
    color = paleta.ALGORITMO[algoritmo]
    i0 = len(fig.data)
    fig.add_trace(go.Scatter(x=[], y=[], mode="markers", name="Alcanzados", hoverinfo="skip",
                             marker=dict(size=6, color=paleta.ALGORITMO_CLARO[algoritmo])), row=1, col=1)
    fig.add_trace(go.Scatter(x=[], y=[], mode="markers", name="Paso actual", hoverinfo="skip",
                             marker=dict(size=7, color=paleta.FRENTE)), row=1, col=1)
    fig.add_trace(go.Scatter(x=[], y=[], mode="lines", name=f"Ruta {NOMBRE[algoritmo]}", hoverinfo="skip",
                             line=dict(color=color, width=4)), row=1, col=1)
    for t in _marcadores(pos, inicio, destinos):
        fig.add_trace(t, row=1, col=1)
    c0 = len(fig.data)
    _panel_codigo(fig, algoritmo, estados[0], col=2)

    frames, nombres = [], []
    for k, e in enumerate(estados):
        ex, ey = _xy(pos, e["exp"])
        fx, fy = _xy(pos, e["frente"])
        rx, ry = _xy(pos, e["ruta"])
        frames.append(go.Frame(name=str(k), traces=[i0, i0 + 1, i0 + 2, c0, c0 + 1, c0 + 2],
                               layout=dict(title_text=e["texto"]),
                               data=[go.Scatter(x=ex, y=ey), go.Scatter(x=fx, y=fy), go.Scatter(x=rx, y=ry)]
                               + _frame_codigo(algoritmo, e)))
        nombres.append(str(k))
    fig.frames = frames
    _controles(fig, nombres)
    return fig


def explorar_flujo(nodos, aristas, estados, niveles=None):
    """Video de Edmonds-Karp con su pseudocódigo: caminos de aumento y corte mínimo."""
    pos = _pos(nodos)
    fig = _lienzo_con_codigo(estados[0]["texto"])
    for t in _trazas_base(nodos, aristas, niveles):
        fig.add_trace(t, row=1, col=1)
    ek = paleta.ALGORITMO["edmonds_karp"]
    i0 = len(fig.data)
    fig.add_trace(go.Scatter(x=[], y=[], mode="lines", name="Pasillos con flujo", hoverinfo="skip",
                             line=dict(color=paleta.SUAVE, width=1.6)), row=1, col=1)
    fig.add_trace(go.Scatter(x=[], y=[], mode="lines", name="Camino de aumento", hoverinfo="skip",
                             line=dict(color=paleta.ALGORITMO["bfs"], width=4)), row=1, col=1)
    fig.add_trace(go.Scatter(x=[], y=[], mode="lines", name="Corte mínimo", hoverinfo="skip",
                             line=dict(color=ek, width=6)), row=1, col=1)
    c0 = len(fig.data)
    _panel_codigo(fig, "edmonds_karp", estados[0], col=2)
    frames, nombres = [], []
    for k, e in enumerate(estados):
        ux, uy = _segmentos(pos, e["usados"])
        cx, cy = _segmentos(pos, e["camino"])
        kx, ky = _segmentos(pos, e["corte"])
        frames.append(go.Frame(name=str(k), traces=[i0, i0 + 1, i0 + 2, c0, c0 + 1, c0 + 2],
                               layout=dict(title_text=e["texto"]),
                               data=[go.Scatter(x=ux, y=uy), go.Scatter(x=cx, y=cy), go.Scatter(x=kx, y=ky)]
                               + _frame_codigo("edmonds_karp", e)))
        nombres.append(str(k))
    fig.frames = frames
    _controles(fig, nombres, ms=260)
    return fig


# ---------- Comparar: dos algoritmos sincronizados por trabajo ----------

def comparar(nodos, aristas, estados_por_alg, inicio, destinos, cuadros=100):
    """BFS y Bellman-Ford lado a lado con un solo reproductor.

    El reloj común es el TRABAJO (aristas revisadas): en el cuadro f ambos han hecho
    a lo sumo f/cuadros del trabajo del más costoso. Así se ve cuánto antes termina BFS.
    """
    pos = _pos(nodos)
    algs = list(estados_por_alg)
    fig = make_subplots(rows=1, cols=len(algs), horizontal_spacing=0.02, subplot_titles=[NOMBRE[a] for a in algs])
    _estilo(fig, "", alto=560)
    animadas = {}
    for c, alg in enumerate(algs, 1):
        for t in _trazas_base(nodos, aristas, mostrar_leyenda=(c == 1)):
            fig.add_trace(t, row=1, col=c)
        animadas[alg] = len(fig.data)
        fig.add_trace(go.Scatter(x=[], y=[], mode="markers", hoverinfo="skip", showlegend=False,
                                 marker=dict(size=5, color=paleta.ALGORITMO_CLARO[alg])), row=1, col=c)
        fig.add_trace(go.Scatter(x=[], y=[], mode="markers", hoverinfo="skip", showlegend=False,
                                 marker=dict(size=6, color=paleta.FRENTE)), row=1, col=c)
        fig.add_trace(go.Scatter(x=[], y=[], mode="lines", hoverinfo="skip", name=f"Ruta {NOMBRE[alg]}",
                                 line=dict(color=paleta.ALGORITMO[alg], width=4)), row=1, col=c)
        for t in _marcadores(pos, inicio, destinos, leyenda=(c == 1)):
            fig.add_trace(t, row=1, col=c)
        fig.update_yaxes(scaleanchor=f"x{'' if c == 1 else c}", row=1, col=c)
    for a in fig.layout.annotations:
        a.update(font=dict(family=paleta.SERIF, size=15, color=paleta.TINTA))

    total = max(estados_por_alg[a][-1]["trabajo"] for a in algs)
    frames, nombres = [], []
    for f in range(cuadros):
        limite = total * (f + 1) / cuadros
        datos, indices, titulos = [], [], []
        for alg in algs:
            est = estados_por_alg[alg]
            k = max([i for i, e in enumerate(est) if e["trabajo"] <= limite] or [0])
            e = est[k]
            ex, ey = _xy(pos, e["exp"])
            fx, fy = _xy(pos, e["frente"])
            rx, ry = _xy(pos, e["ruta"])
            datos += [go.Scatter(x=ex, y=ey), go.Scatter(x=fx, y=fy), go.Scatter(x=rx, y=ry)]
            indices += [animadas[alg], animadas[alg] + 1, animadas[alg] + 2]
            estado = "terminado" if k == len(est) - 1 else "buscando"
            titulos.append(f"{NOMBRE[alg]} · {estado} · {_miles(e['trabajo'])} aristas revisadas")
        anots = [dict(text=t, font=dict(family=paleta.SERIF, size=15, color=paleta.TINTA)) for t in titulos]
        frames.append(go.Frame(name=str(f), traces=indices, data=datos,
                               layout=dict(annotations=[{**fig.layout.annotations[i].to_plotly_json(), **anots[i]}
                                                        for i in range(len(algs))])))
        nombres.append(str(f))
    fig.frames = frames
    _controles(fig, nombres, ms=120)
    return fig


# ---------- Historia: el operario y el pasillo bloqueado ----------

FASES = ["Explora", "Traza la ruta", "Un robot bloquea el paso", "Recalcula"]


def _titulo_fase(n, detalle):
    partes = [f"<b>{i} {f}</b>" if i == n else f"<span style='color:{paleta.SUAVE}'>{i} {f}</span>"
              for i, f in enumerate(FASES, 1)]
    return "  ·  ".join(partes) + f"<br><span style='font-size:13px;color:{paleta.SUAVE}'>{detalle}</span>"


def historia(nodos, aristas, ady, inicio, destino):
    """Un operario va de `inicio` a `destino` con Bellman-Ford; a mitad de camino un robot
    averiado bloquea una ubicación de su ruta y recalcula desde donde está."""
    pos = _pos(nodos)
    dirigidas = [(u, v, w) for u, vec in ady.items() for v, w in vec]
    pasos1 = []
    dist, padre, _ = bf.bellman_ford(ady.keys(), dirigidas, inicio, pasos1)
    ruta1 = reconstruir(padre, destino)
    k = max(1, len(ruta1) // 3)
    bloqueado = ruta1[min(k + 3, len(ruta1) - 2)]
    ady2 = {u: [(v, w) for v, w in vec if v != bloqueado] for u, vec in ady.items() if u != bloqueado}
    dirigidas2 = [(u, v, w) for u, vec in ady2.items() for v, w in vec]
    pasos2 = []
    dist2, padre2, _ = bf.bellman_ford(ady2.keys(), dirigidas2, ruta1[k], pasos2)
    ruta2 = reconstruir(padre2, destino)

    fig = go.Figure(_trazas_base(nodos, aristas, opacidad=0.25))
    _estilo(fig, "", alto=520)
    fig.update_yaxes(scaleanchor="x")
    fig.update_layout(title=dict(font=dict(family=paleta.SANS, size=14)))
    capas = [("Alcanzados", "markers", dict(size=5, color=paleta.ALGORITMO_CLARO["bellman_ford"]), None),
             ("Ruta", "lines", None, dict(color=paleta.ALGORITMO["bellman_ford"], width=4)),
             ("Nueva ruta", "lines", None, dict(color=paleta.ALGORITMO["bfs"], width=4, dash="dot")),
             ("Bloqueo", "markers", dict(size=18, symbol="x", color=paleta.ALGORITMO["edmonds_karp"]), None),
             ("Operario", "markers", dict(size=15, symbol="diamond", color=paleta.TINTA,
                                          line=dict(color=paleta.TARJETA, width=2)), None)]
    i0 = len(fig.data)
    for nombre, modo, marker, line in capas:
        fig.add_trace(go.Scatter(x=[], y=[], mode=modo, name=nombre, hoverinfo="skip", marker=marker, line=line))
    for t in _marcadores(pos, inicio, [destino]):
        fig.add_trace(t)

    cuadros = []

    def cuadro(alc, r1, r2, bloq, op, titulo):
        cuadros.append((alc, r1, r2, bloq, op, titulo))

    vistos = []
    for j in _agrupar(len(pasos1), 12):
        vistos = sorted(set(vistos) | {n for e in pasos1[: j + 1] for n in e})
        cuadro(vistos, [], [], [], [inicio], _titulo_fase(1, f"Bellman-Ford, ronda {j + 1}: "
                                                              f"{len(vistos)} ubicaciones alcanzadas"))
    for j in _agrupar(k + 1, 12):
        cuadro([], ruta1, [], [], [ruta1[j]], _titulo_fase(2, f"Ruta de {len(ruta1) - 1} pasillos con la "
                                                              f"congestión de hora punta"))
    for _ in range(6):
        cuadro([], ruta1, [], [bloqueado], [ruta1[k]], _titulo_fase(3, f"Un robot se avería en {bloqueado}: "
                                                                       "esa ubicación deja de existir en el grafo"))
    vistos = []
    for j in _agrupar(len(pasos2), 10):
        vistos = sorted(set(vistos) | {n for e in pasos2[: j + 1] for n in e})
        cuadro(vistos, ruta1[: k + 1], [], [bloqueado], [ruta1[k]],
               _titulo_fase(4, f"Recalcula desde {ruta1[k]}, sin volver a empezar: ronda {j + 1}"))
    for j in _agrupar(len(ruta2), 14):
        cuadro([], ruta1[: k + 1], ruta2, [bloqueado], [ruta2[j]],
               _titulo_fase(4, f"Nuevo camino: {len(ruta2) - 1} pasillos desde donde estaba"))

    frames, nombres = [], []
    for f, (alc, r1, r2, bloq, op, titulo) in enumerate(cuadros):
        datos = [go.Scatter(x=_xy(pos, alc)[0], y=_xy(pos, alc)[1]),
                 go.Scatter(x=_xy(pos, r1)[0], y=_xy(pos, r1)[1]),
                 go.Scatter(x=_xy(pos, r2)[0], y=_xy(pos, r2)[1]),
                 go.Scatter(x=_xy(pos, bloq)[0], y=_xy(pos, bloq)[1]),
                 go.Scatter(x=_xy(pos, op)[0], y=_xy(pos, op)[1])]
        frames.append(go.Frame(name=str(f), traces=list(range(i0, i0 + 5)), data=datos,
                               layout=dict(title_text=titulo)))
        nombres.append(str(f))
    fig.frames = frames
    fig.update_layout(title_text=cuadros[0][5])
    _controles(fig, nombres, ms=140)
    return fig, {"ruta": ruta1, "bloqueado": bloqueado, "nueva": ruta2, "desde": ruta1[k]}


# ---------- compatibilidad: versiones simples usadas por la simulación y los tests ----------

def animacion_busqueda(nodos, aristas, registro, algoritmo, inicio, destinos, max_cuadros=150, ady=None):
    if ady is None:
        from . import grafo
        ady = grafo.adyacencia(aristas)
    n_dir = sum(len(v) for v in ady.values())
    estados = estados_busqueda(registro, algoritmo, inicio, ady, n_dir, max_cuadros)
    return explorar(nodos, aristas, estados, algoritmo, inicio, destinos)


def animacion_flujo(nodos, aristas, pasos, cuellos, lado_fuente=None, niveles=None, titulo=""):
    return explorar_flujo(nodos, aristas, estados_flujo(pasos, cuellos), niveles)


def animacion_turno(nodos, aristas, operarios, max_cuadros=60):
    """Video del turno: los operarios se mueven y los pasillos se 'calientan' con cada cruce."""
    pos = _pos(nodos)
    fig = go.Figure(_trazas_base(nodos, aristas, opacidad=0.15))
    _estilo(fig, "Turno simulado")
    fig.update_yaxes(scaleanchor="x")
    duracion = max(len(op["camino"]) for op in operarios)
    tiempos = _agrupar(duracion, max_cuadros)
    maximo = max(simulacion.uso_hasta(operarios, duracion).values())
    fig.add_trace(go.Scatter(x=[], y=[], mode="markers", name="Cruces por pasillo", hoverinfo="skip",
                             marker=dict(size=7, color=[], colorscale=paleta.CALOR, cmin=0, cmax=maximo,
                                         showscale=True, colorbar=dict(title="Cruces", x=1.0, thickness=10,
                                                                       outlinewidth=0))))
    fig.add_trace(go.Scatter(x=[], y=[], mode="markers", name="Operarios", hoverinfo="skip",
                             marker=dict(size=12, color=paleta.TINTA, symbol="diamond",
                                         line=dict(color=paleta.TARJETA, width=1.5))))
    frames, nombres = [], []
    for t in tiempos:
        uso = simulacion.uso_hasta(operarios, t)
        pares = [tuple(p) for p in uso]
        mx = [(pos[u][0] + pos[v][0]) / 2 for u, v in pares]
        my = [(pos[u][1] + pos[v][1]) / 2 for u, v in pares]
        ox, oy = _xy(pos, [simulacion.posicion(op, t) for op in operarios])
        activos = sum(t < len(op["camino"]) - 1 for op in operarios)
        frames.append(go.Frame(name=str(t), traces=[4, 5],
                               layout=dict(title_text=f"Paso {t} de {duracion - 1} · {activos} operarios "
                                                      f"trabajando · {len(pares)} pasillos usados"),
                               data=[go.Scatter(x=mx, y=my, marker=dict(color=[uso[frozenset(p)] for p in pares])),
                                     go.Scatter(x=ox, y=oy)]))
        nombres.append(str(t))
    fig.frames = frames
    _controles(fig, nombres, ms=200)
    return fig
