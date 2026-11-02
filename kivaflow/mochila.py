"""Mochila 0/1 con programación dinámica (módulo 12, casos de uso).

En el almacén: un robot lleva hasta W kg. De los productos de un pedido grande hay
que elegir cuáles van en el primer viaje para maximizar la urgencia total.
"""


def mochila_01(pesos, valores, capacidad):
    """dp[i][c] = mejor valor con los primeros i productos y capacidad c. O(n · W)."""
    n = len(pesos)
    dp = [[0] * (capacidad + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        p, v = pesos[i - 1], valores[i - 1]
        for c in range(capacidad + 1):
            dp[i][c] = dp[i - 1][c]  # no lo llevo
            if p <= c and dp[i - 1][c - p] + v > dp[i][c]:
                dp[i][c] = dp[i - 1][c - p] + v  # lo llevo
    elegidos, c = [], capacidad
    for i in range(n, 0, -1):  # reconstruir desde la última celda
        if dp[i][c] != dp[i - 1][c]:
            elegidos.append(i - 1)
            c -= pesos[i - 1]
    return dp[n][capacidad], sorted(elegidos), dp
