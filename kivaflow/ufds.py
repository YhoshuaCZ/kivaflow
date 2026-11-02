"""UFDS (Union-Find Disjoint Sets): dice si dos ubicaciones ya están conectadas.

Kruskal lo usa para no formar ciclos: si `unir(a, b)` devuelve False, a y b ya
estaban en el mismo grupo y el pasillo a-b cerraría un ciclo.
"""


class UFDS:
    def __init__(self, elementos):
        self.padre = {e: e for e in elementos}
        self.rango = {e: 0 for e in elementos}
        self.grupos = len(self.padre)

    def buscar(self, x):
        """Representante del grupo de x, con compresión de caminos."""
        raiz = x
        while self.padre[raiz] != raiz:
            raiz = self.padre[raiz]
        while self.padre[x] != raiz:  # cada nodo del camino apunta directo a la raíz
            self.padre[x], x = raiz, self.padre[x]
        return raiz

    def unir(self, a, b):
        """Une los grupos de a y b. Devuelve False si ya estaban unidos."""
        ra, rb = self.buscar(a), self.buscar(b)
        if ra == rb:
            return False
        if self.rango[ra] < self.rango[rb]:  # unión por rango: el árbol bajo cuelga del alto
            ra, rb = rb, ra
        self.padre[rb] = ra
        if self.rango[ra] == self.rango[rb]:
            self.rango[ra] += 1
        self.grupos -= 1
        return True
