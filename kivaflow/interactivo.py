"""Figuras interactivas (Plotly) para la app: mapa clicable y animaciones tipo video.

Las animaciones se arman con los PASOS que anotan los propios algoritmos
(`pasos=` en bfs, bellman_ford y edmonds_karp): lo que se ve es lo que hizo el
algoritmo, no una imitación. Plotly reproduce los cuadros en el navegador
(play, pausa, velocidad y barra para adelantar o retroceder) sin volver a calcular.
"""
import math

import plotly.graph_objects as go

from . import simulacion
from .visual import COLOR_NIVEL_FUERTE, COLOR_NIVEL_SUAVE, COLOR_ZONA

ALTO = 680
COLOR_ALGORITMO = {"bfs": "#2b6cb0", "bellman_ford": "#2f855a"}
NOMBRE = {"bfs": "BFS", "bellman_ford": "Bellman-Ford"}
NODOS_TRAZA = 3  # índice de la traza de nodos (la que se puede cliquear)


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


def base(nodos, aristas, niveles=None, suave=True):
    """Trazas 0-2: pasillos por congestión; traza 3: nodos (clicables)."""
    pos = _pos(nodos)
    colores = COLOR_NIVEL_SUAVE if suave else COLOR_NIVEL_FUERTE
    fig = go.Figure()
    for nivel in ("Baja", "Media", "Alta"):
        pares = [(a["Nodo_Origen"], a["Nodo_Destino"]) for a in aristas
                 if (niveles[(a["Nodo_Origen"], a["Nodo_Destino"])] if niveles else a["Frecuencia_Pedidos"]) == nivel]
        x, y = _segmentos(pos, pares)
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines", line=dict(color=colores[nivel], width=2.5 if nivel == "Alta" else 1.8),
                                 hoverinfo="skip", name=f"Congestión {nivel.lower()}"))
    ids = list(nodos)
    x, y = _xy(pos, ids)
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="markers", name="Ubicaciones", customdata=ids,
        marker=dict(size=5, color=[COLOR_ZONA[nodos[i]["Zona"]] for i in ids], opacity=0.3,
                    symbol=["square" if nodos[i]["Tipo"] == "estacion" else "circle" for i in ids]),
        text=[f"{i} · {nodos[i]['Zona']} · {nodos[i]['Tipo']}" + (f" · {nodos[i]['SKU']}" if nodos[i]["SKU"] else "")
              for i in ids],
        hovertemplate="%{text}<extra></extra>"))
    fig.update_layout(height=ALTO, margin=dict(l=10, r=10, t=50, b=10), dragmode="pan",
                      legend=dict(orientation="h", y=-0.02), plot_bgcolor="white",
                      xaxis=dict(showgrid=False, zeroline=False, title="x (m)"),
                      yaxis=dict(showgrid=False, zeroline=False, scaleanchor="x", title="y (m)"))
    return fig


def _marcadores(fig, pos, inicio, destinos):
    if destinos:
        x, y = _xy(pos, destinos)
        fig.add_trace(go.Scatter(x=x, y=y, mode="markers", name="Destinos",
                                 marker=dict(size=14, color="#c53030", line=dict(color="white", width=1)),
                                 hoverinfo="skip"))
    if inicio:
        fig.add_trace(go.Scatter(x=[pos[inicio][0]], y=[pos[inicio][1]], mode="markers", name="Inicio",
                                 marker=dict(size=18, color="black", symbol="square"), hoverinfo="skip"))


def mapa(nodos, aristas, inicio=None, destinos=(), rutas=None):
    """Mapa para elegir puntos con clic. rutas: {algoritmo: camino} para dibujarlas encima."""
    pos = _pos(nodos)
    fig = base(nodos, aristas)
    for alg, camino in (rutas or {}).items():
        x, y = _xy(pos, camino)
        fig.add_trace(go.Scatter(x=x, y=y, mode="lines", name=f"Ruta {NOMBRE[alg]}", hoverinfo="skip",
                                 line=dict(color=COLOR_ALGORITMO[alg], width=5 if alg == "bfs" else 3)))
    _marcadores(fig, pos, inicio, destinos)
    fig.update_layout(title="Haz clic en una ubicación para marcarla")
    return fig


def _controles(fig, nombres, ms=150):
    """Botones play (x0.5, x1, x2, x4) y pausa + barra para moverse por los cuadros."""
    def play(d):
        return [None, {"frame": {"duration": d, "redraw": False}, "fromcurrent": True,
                       "transition": {"duration": 0}, "mode": "immediate"}]

    botones = [dict(label=f"▶ x{v:g}", method="animate", args=play(ms / v)) for v in (0.5, 1, 2, 4)]
    botones.append(dict(label="⏸", method="animate",
                        args=[[None], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}]))
    fig.update_layout(
        updatemenus=[dict(type="buttons", direction="left", x=0, y=1.08, xanchor="left", yanchor="bottom",
                          showactive=False, buttons=botones)],
        sliders=[dict(active=0, x=0, len=1, y=0, yanchor="top", pad=dict(t=30),
                      currentvalue=dict(prefix="Cuadro: "),
                      steps=[dict(label=str(i + 1), method="animate",
                                  args=[[n], {"frame": {"duration": 0, "redraw": False}, "mode": "immediate"}])
                             for i, n in enumerate(nombres)])])


def _agrupar(n, maximo):
    """Índices de corte para mostrar n pasos en a lo sumo `maximo` cuadros."""
    if n <= maximo:
        return list(range(n))
    paso = math.ceil(n / maximo)
    return list(range(paso - 1, n, paso)) + ([n - 1] if (n - 1) % paso else [])


def animacion_busqueda(nodos, aristas, registro, algoritmo, inicio, destinos, max_cuadros=150):
    """Video de BFS (por niveles) o Bellman-Ford (por rondas), tramo por tramo, y la ruta final."""
    pos = _pos(nodos)
    fig = base(nodos, aristas)
    color = COLOR_ALGORITMO[algoritmo]
    # Trazas animadas: 4 explorados, 5 frente actual, 6 ruta acumulada
    fig.add_trace(go.Scatter(x=[], y=[], mode="markers", name="Explorados",
                             marker=dict(size=7, color=color, opacity=0.25), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[], y=[], mode="markers", name="Frente (nivel / ronda actual)",
                             marker=dict(size=9, color="#dd6b20"), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[], y=[], mode="lines", name=f"Ruta {NOMBRE[algoritmo]}",
                             line=dict(color=color, width=5), hoverinfo="skip"))
    _marcadores(fig, pos, inicio, destinos)

    por_tramo = max(5, max_cuadros // max(1, len(registro)))
    cuadros, ruta = [], [inicio]
    for i, r in enumerate(registro, 1):
        if algoritmo == "bfs":
            grupos = {}
            for u, nivel in r["pasos"]:
                grupos.setdefault(nivel, []).append(u)
            etapas = [grupos[k] for k in sorted(grupos)]
            unidad = "nivel"
        else:
            etapas = r["pasos"]
            unidad = "ronda"
        vistos, explorados, acumulados = set(), [], []
        for e in etapas:
            for n in e:
                if n not in vistos:
                    vistos.add(n)
                    explorados.append(n)
            acumulados.append((list(explorados), e))
        for j in _agrupar(len(acumulados), por_tramo):
            exp, frente = acumulados[j]
            cuadros.append((exp, frente, list(ruta),
                            f"{NOMBRE[algoritmo]} · tramo {i}/{len(registro)} · {unidad} {j + 1}/{len(acumulados)}"
                            f" · {len(exp)} nodos alcanzados"))
        ruta += r["tramo"][1:]
        cuadros.append(([], [], list(ruta), f"{NOMBRE[algoritmo]} · tramo {i}/{len(registro)} listo · "
                                            f"ruta de {len(ruta) - 1} pasillos"))

    frames, nombres = [], []
    for k, (exp, frente, rt, titulo) in enumerate(cuadros):
        ex, ey = _xy(pos, exp)
        fx, fy = _xy(pos, frente)
        rx, ry = _xy(pos, rt)
        frames.append(go.Frame(name=str(k), traces=[4, 5, 6], layout=dict(title=titulo),
                               data=[go.Scatter(x=ex, y=ey), go.Scatter(x=fx, y=fy), go.Scatter(x=rx, y=ry)]))
        nombres.append(str(k))
    fig.frames = frames
    fig.update_layout(title=cuadros[0][3] if cuadros else "")
    _controles(fig, nombres)
    return fig


def animacion_flujo(nodos, aristas, pasos, cuellos, lado_fuente, niveles=None, titulo=""):
    """Video de Edmonds-Karp: cada camino de aumento, el flujo acumulado y al final el corte mínimo."""
    pos = _pos(nodos)
    fig = base(nodos, aristas, niveles)
    # Trazas animadas: 4 pasillos ya usados, 5 camino actual, 6 corte mínimo
    fig.add_trace(go.Scatter(x=[], y=[], mode="lines", name="Pasillos con flujo",
                             line=dict(color="#4a5568", width=2), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[], y=[], mode="lines", name="Camino de aumento actual",
                             line=dict(color="#2b6cb0", width=5), hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=[], y=[], mode="lines", name="Corte mínimo (cuellos de botella)",
                             line=dict(color="#c53030", width=6), hoverinfo="skip"))
    frames, nombres, usados, total = [], [], [], 0
    for k, (camino, delta) in enumerate(pasos):
        reales = [n for n in camino if n in pos]
        pares = list(zip(reales, reales[1:]))
        usados += pares
        total += delta
        ux, uy = _segmentos(pos, usados)
        cx, cy = _segmentos(pos, pares)
        frames.append(go.Frame(name=str(k), traces=[4, 5, 6],
                               layout=dict(title=f"Camino de aumento {k + 1}/{len(pasos)} · +{delta:g} · "
                                                 f"flujo acumulado {total:g} operarios/min"),
                               data=[go.Scatter(x=ux, y=uy), go.Scatter(x=cx, y=cy), go.Scatter(x=[], y=[])]))
        nombres.append(str(k))
    ux, uy = _segmentos(pos, usados)
    kx, ky = _segmentos(pos, [(u, v) for u, v, _ in cuellos])
    frames.append(go.Frame(name="fin", traces=[4, 5, 6],
                           layout=dict(title=f"Sin más caminos: flujo máximo {total:g} = corte mínimo "
                                             f"({len(cuellos)} pasillos saturados)"),
                           data=[go.Scatter(x=ux, y=uy), go.Scatter(x=[], y=[]), go.Scatter(x=kx, y=ky)]))
    nombres.append("fin")
    fig.frames = frames
    fig.update_layout(title=titulo or "Edmonds-Karp: dale ▶")
    _controles(fig, nombres, ms=250)
    return fig


def animacion_turno(nodos, aristas, operarios, max_cuadros=60):
    """Video del turno: los operarios se mueven y los pasillos se 'calientan' con cada cruce."""
    pos = _pos(nodos)
    fig = base(nodos, aristas)
    fig.data[3].marker.opacity = 0.15
    duracion = max(len(op["camino"]) for op in operarios)
    tiempos = _agrupar(duracion, max_cuadros)
    maximo = max(simulacion.uso_hasta(operarios, duracion).values())
    # Trazas animadas: 4 calor de pasillos (punto medio), 5 operarios
    fig.add_trace(go.Scatter(x=[], y=[], mode="markers", name="Cruces por pasillo", hoverinfo="skip",
                             marker=dict(size=7, color=[], colorscale="YlOrRd", cmin=0, cmax=maximo,
                                         showscale=True, colorbar=dict(title="Cruces", x=1.02))))
    fig.add_trace(go.Scatter(x=[], y=[], mode="markers", name="Operarios", hoverinfo="skip",
                             marker=dict(size=13, color="#2b6cb0", symbol="diamond",
                                         line=dict(color="white", width=1))))
    frames, nombres = [], []
    for t in tiempos:
        uso = simulacion.uso_hasta(operarios, t)
        pares = [tuple(p) for p in uso]
        mx = [(pos[u][0] + pos[v][0]) / 2 for u, v in pares]
        my = [(pos[u][1] + pos[v][1]) / 2 for u, v in pares]
        ox, oy = _xy(pos, [simulacion.posicion(op, t) for op in operarios])
        activos = sum(t < len(op["camino"]) - 1 for op in operarios)
        frames.append(go.Frame(name=str(t), traces=[4, 5],
                               layout=dict(title=f"Paso {t}/{duracion - 1} · {activos} operarios trabajando · "
                                                 f"{len(pares)} pasillos usados"),
                               data=[go.Scatter(x=mx, y=my, marker=dict(color=[uso[frozenset(p)] for p in pares])),
                                     go.Scatter(x=ox, y=oy)]))
        nombres.append(str(t))
    fig.frames = frames
    fig.update_layout(title="Turno simulado: dale ▶")
    _controles(fig, nombres, ms=200)
    return fig
