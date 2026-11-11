"""Orden óptimo de visita de un pedido con programación dinámica (Held-Karp).

Decidir en qué orden recoger n productos es el problema del viajante (NP-difícil):
por fuerza bruta hay n! órdenes. La regla voraz de `pedido.py` (ir siempre al
pendiente más cercano) es rápida pero no garantiza el mejor recorrido.

Held y Karp (1962) lo resuelven exacto con DP sobre subconjuntos:

    dp[S][j] = menor costo de salir del origen, visitar exactamente los productos
               del conjunto S y terminar en j (j ∈ S)
    dp[{j}][j] = d(origen, j)
    dp[S][j]   = min sobre i ∈ S − {j} de  dp[S − {j}][i] + d(i, j)

Son n · 2ⁿ⁻¹ estados y cada uno mira hasta n anteriores: O(n² · 2ⁿ) en tiempo y
O(n · 2ⁿ) en memoria. Sigue siendo exponencial, pero con 10 productos son 5120
estados en vez de 10! = 3 628 800 órdenes; por eso se limita a pedidos chicos.
"""
from kivaflow.caminos import camino

INF = float("inf")
MAX_PRODUCTOS = 12  # 12 · 2¹¹ ≈ 24 500 estados; con 20 ya serían 10 millones


def held_karp(d_origen, d, d_final=None):
    """Orden óptimo de n productos (índices 0..n-1).

    d_origen[j]: costo del origen al producto j · d[i][j]: costo entre productos ·
    d_final[j]: costo de cerrar el recorrido después de j (0 si no se da).
    Devuelve (orden, costo, estados calculados). Los conjuntos S son máscaras de bits.
    """
    n = len(d_origen)
    if n == 0:
        return [], 0.0, 0
    d_final = d_final or [0.0] * n
    dp = [[INF] * n for _ in range(1 << n)]
    previo = [[None] * n for _ in range(1 << n)]
    for j in range(n):
        dp[1 << j][j] = d_origen[j]
    estados = n
    for S in range(1, 1 << n):
        for j in range(n):
            if not S & (1 << j) or S == 1 << j:
                continue
            sin_j = S ^ (1 << j)
            estados += 1
            for i in range(n):
                if sin_j & (1 << i) and dp[sin_j][i] + d[i][j] < dp[S][j]:
                    dp[S][j] = dp[sin_j][i] + d[i][j]
                    previo[S][j] = i
    todos = (1 << n) - 1
    ultimo = min(range(n), key=lambda j: dp[todos][j] + d_final[j])
    costo = dp[todos][ultimo] + d_final[ultimo]
    orden, S, j = [], todos, ultimo
    while j is not None:  # reconstruir hacia atrás con `previo`
        orden.append(j)
        S, j = S ^ (1 << j), previo[S][j]
    return orden[::-1], costo, estados


def ruta_optima(buscador, origen, productos, muelles_finales=()):
    """Como `pedido.ruta_pedido`, pero con el orden de visita óptimo.

    Hace una búsqueda desde el origen y una desde cada producto (n + 1 en total,
    las mismas que el voraz) para armar la matriz de distancias; después Held-Karp
    elige el orden. Devuelve (recorrido completo, orden de visita).
    """
    productos = list(dict.fromkeys(productos))
    if len(productos) > MAX_PRODUCTOS:
        raise ValueError(f"El orden óptimo se limita a {MAX_PRODUCTOS} productos (crece como n² · 2ⁿ).")
    if not productos:
        return [origen], []
    dist_o, padre_o = buscador.desde(origen)
    busquedas = [buscador.desde(p) for p in productos]
    d = [[dist.get(q, INF) for q in productos] for dist, _ in busquedas]
    muelle = [min(muelles_finales, key=lambda m: (dist.get(m, INF), m)) if muelles_finales else None
              for dist, _ in busquedas]
    d_final = [dist.get(m, INF) if m else 0.0 for (dist, _), m in zip(busquedas, muelle)]
    indices, _, estados = held_karp([dist_o.get(p, INF) for p in productos], d, d_final)
    buscador.ops["estados de la DP (n · 2ⁿ⁻¹)"] += estados

    recorrido = camino(padre_o, productos[indices[0]])
    for a, b in zip(indices, indices[1:]):
        recorrido += camino(busquedas[a][1], productos[b])[1:]
    orden = [productos[i] for i in indices]
    if muelles_finales:
        ultimo = indices[-1]
        recorrido += camino(busquedas[ultimo][1], muelle[ultimo])[1:]
        orden.append(muelle[ultimo])
    return recorrido, orden
