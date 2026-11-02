"""Flujo máximo con Ford-Fulkerson (hoja 11, ejercicio 2), programado a mano.

Red: cada pasillo se puede cruzar en los dos sentidos con una capacidad en
operarios por minuto (3, 2 o 1 según su congestión). Una superfuente se conecta a
los muelles de Recepción y los muelles de Despacho a un supersumidero.

Ford-Fulkerson es un método: no dice cómo buscar el camino aumentante.
- `ford_fulkerson` lo busca con DFS, como en el cuaderno de la clase. Su costo depende
  del valor del flujo: O(E · f*).
- `edmonds_karp` lo busca con BFS, así que siempre toma el camino con menos arcos.
  Eso acota las iteraciones a O(V · E) y el total a O(V · E²), sin importar las
  capacidades (Edmonds y Karp, 1972). Es la variante que usa el informe.
"""
from collections import deque
from dataclasses import dataclass, field

FUENTE, SUMIDERO = "S*", "T*"
INF = float("inf")


@dataclass
class Flujo:
    valor: int = 0
    caminos: list = field(default_factory=list)  # [(camino, cuello_de_botella), ...]
    lado_fuente: set = field(default_factory=set)  # conjunto S del corte mínimo
    corte: list = field(default_factory=list)  # pasillos (u, v, capacidad) que cruzan el corte
    usos_inversos: int = 0  # veces que un camino aumentante usó un arco inverso


def red(aristas_csv, capacidad, fuentes, sumideros):
    """Capacidades residuales {u: {v: c}} con superfuente y supersumidero."""
    cap = {}

    def arco(u, v, c):
        cap.setdefault(u, {}).setdefault(v, 0)
        cap.setdefault(v, {}).setdefault(u, 0)  # arco inverso, empieza en 0
        cap[u][v] += c

    for a in aristas_csv:
        c = capacidad[a["Frecuencia_Pedidos"]]
        arco(a["Nodo_Origen"], a["Nodo_Destino"], c)
        arco(a["Nodo_Destino"], a["Nodo_Origen"], c)
    for f in fuentes:
        arco(FUENTE, f, INF)
    for t in sumideros:
        arco(t, SUMIDERO, INF)
    return cap


def _dfs(res, s, t):
    """Un camino s -> t con capacidad residual > 0 (DFS iterativo)."""
    padre, pila = {s: None}, [s]
    while pila:
        u = pila.pop()
        if u == t:
            break
        for v, c in res[u].items():
            if c > 0 and v not in padre:
                padre[v] = u
                pila.append(v)
    if t not in padre:
        return None
    camino, x = [], t
    while x is not None:
        camino.append(x)
        x = padre[x]
    return camino[::-1]


def _bfs(res, s, t):
    """El camino s -> t con capacidad residual > 0 y con menos arcos (BFS)."""
    padre, cola = {s: None}, deque([s])
    while cola and t not in padre:
        u = cola.popleft()
        for v, c in res[u].items():
            if c > 0 and v not in padre:
                padre[v] = u
                cola.append(v)
    if t not in padre:
        return None
    camino, x = [], t
    while x is not None:
        camino.append(x)
        x = padre[x]
    return camino[::-1]


def edmonds_karp(cap, s=FUENTE, t=SUMIDERO):
    """Ford-Fulkerson con BFS. O(V · E²)."""
    return ford_fulkerson(cap, s, t, buscar=_bfs)


def ford_fulkerson(cap, s=FUENTE, t=SUMIDERO, buscar=_dfs):
    """Aumenta el flujo por caminos de la red residual hasta que no quede ninguno.
    `buscar` elige cómo se halla el camino: DFS (por defecto) o BFS (Edmonds-Karp)."""
    original = {u: dict(vs) for u, vs in cap.items()}
    res = {u: dict(vs) for u, vs in cap.items()}
    f = Flujo()
    while (camino := buscar(res, s, t)) is not None:
        pares = list(zip(camino, camino[1:]))
        cuello = min(res[u][v] for u, v in pares)
        for u, v in pares:
            if original[u][v] == 0:  # se está cancelando flujo de una iteración anterior
                f.usos_inversos += 1
            res[u][v] -= cuello
            res[v][u] += cuello
        f.valor += cuello
        f.caminos.append((camino, cuello))
    # Corte mínimo: lo alcanzable desde s en la red residual final.
    alcanzado, pila = {s}, [s]
    while pila:
        u = pila.pop()
        for v, c in res[u].items():
            if c > 0 and v not in alcanzado:
                alcanzado.add(v)
                pila.append(v)
    f.lado_fuente = alcanzado
    f.corte = [(u, v, original[u][v]) for u in alcanzado for v in original[u]
               if v not in alcanzado and original[u][v] > 0]
    return f
