"""Ruta de un pedido con varios productos: en qué orden visitar los racks.

Visitar k racks en el orden óptimo es el problema del viajero (TSP), NP-difícil:
probar todos los órdenes cuesta O(k!). Se usa la heurística VORAZ del vecino más
cercano: desde donde está el operario, ir al rack pendiente más barato; al final,
volver al muelle. No garantiza el óptimo, pero son solo k + 1 búsquedas.

Las dos estrategias usan la misma heurística; solo cambia cómo se mide "más barato":
- "bfs": número de pasillos (ignora la congestión). BFS se detiene en el primer rack
  pendiente que encuentra, porque por niveles ese es el más cercano.
- "bellman_ford": distancia ajustada por congestión. Bellman-Ford calcula el costo a
  TODOS los nodos en cada búsqueda; no puede cortar antes.
"""
import time

from . import bellman_ford as bf
from . import config
from .bfs import bfs, reconstruir


def muelles_de_despacho(nodos):
    return sorted(n for n, d in nodos.items() if d["Tipo"] == "estacion" and int(d["Columna"]) == config.COLUMNAS - 1)


def aleatorio(nodos, popularidad, k, rng):
    """Un pedido de k productos distintos elegidos según su popularidad.

    Devuelve (muelle, racks): el muelle de despacho de donde sale y los racks a visitar.
    """
    rack_de = {d["SKU"]: n for n, d in nodos.items() if d["SKU"]}
    skus = sorted(rack_de)
    pesos = [popularidad.get(s, 0) + 1 for s in skus]
    elegidos = set()
    while len(elegidos) < k:
        elegidos.add(rng.choices(skus, weights=pesos)[0])
    return rng.choice(muelles_de_despacho(nodos)), [rack_de[s] for s in sorted(elegidos)]


def ruta_pedido(ady, aristas_dirigidas, inicio, racks, estrategia):
    """Devuelve dict con camino completo (lista de nodos), orden de visita y stats."""
    pendientes = set(racks)
    actual, camino, orden = inicio, [inicio], []
    visitados = relajaciones = busquedas = 0
    t0 = time.perf_counter()
    while True:
        volver = not pendientes
        destinos = {inicio} if volver else pendientes
        busquedas += 1
        if estrategia == "bfs":
            tramo, vis = bfs(ady, actual, destinos)
            visitados += vis
        elif estrategia == "bellman_ford":
            dist, padre, stats = bf.bellman_ford(ady.keys(), aristas_dirigidas, actual)
            siguiente = min(sorted(destinos), key=lambda d: dist[d])
            tramo = reconstruir(padre, siguiente)
            visitados += len(ady)
            relajaciones += stats["relajaciones"]
        else:
            raise ValueError(estrategia)
        actual = tramo[-1]
        camino += tramo[1:]
        if volver:
            break
        orden.append(actual)
        pendientes.discard(actual)
    return {
        "camino": camino, "orden": orden, "busquedas": busquedas,
        "nodos_visitados": visitados, "relajaciones": relajaciones,
        "segundos": time.perf_counter() - t0,
    }


def medir(camino, aristas_por_par, perfil="punta"):
    """Pasillos, distancia física, distancia ajustada y tiempo estimado de un camino."""
    factores = config.PERFILES_HORA[perfil]
    fisica = ajustada = 0.0
    for u, v in zip(camino, camino[1:]):
        a = aristas_por_par[frozenset((u, v))]
        d = float(a["Distancia_m"])
        fisica += d
        ajustada += d * factores[a["Frecuencia_Pedidos"]]
    return {"pasillos": len(camino) - 1, "distancia_m": round(fisica, 2),
            "distancia_ajustada_m": round(ajustada, 2), "tiempo_s": round(ajustada / config.VELOCIDAD_M_S, 1)}
