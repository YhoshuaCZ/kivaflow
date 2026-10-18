# Resultados de los experimentos

> Generado por `scripts/experimentos.py`. Demanda: **sintetica**. 30 pedidos por escenario; cada uno sale de un muelle de despacho, visita sus racks en orden de vecino más cercano y vuelve. Los tiempos en ms dependen de la PC. *Nodos visitados* y *relajaciones* suman todas las búsquedas del pedido (k productos = k + 1 búsquedas). *Tiempo* es el tiempo estimado de caminata del operario (distancia ajustada / 1,1 m/s).

## Rutas de picking: BFS vs. Bellman-Ford (promedios por pedido)

| Hora | Productos | Pasillos BFS | Pasillos B-F | Tiempo BFS (s) | Tiempo B-F (s) | Ahorro B-F | Nodos visitados BFS | Relajaciones B-F | ms BFS | ms B-F |
|---|---|---|---|---|---|---|---|---|---|---|
| valle | 1 | 75.5 | 75.5 | 99.4 | 84.5 | 14.9 % | 2278 | 5126 | 0.7 | 43.2 |
| valle | 5 | 144.1 | 144.8 | 187.3 | 165.9 | 11.4 % | 4163 | 15336 | 1.3 | 111.8 |
| valle | 10 | 188.0 | 188.1 | 241.3 | 217.4 | 9.9 % | 4776 | 28174 | 1.5 | 183.1 |
| punta | 1 | 75.5 | 75.8 | 123.3 | 87.5 | 29.1 % | 2278 | 5594 | 0.8 | 42.9 |
| punta | 5 | 144.1 | 145.9 | 229.7 | 175.6 | 23.6 % | 4163 | 16735 | 1.3 | 111.2 |
| punta | 10 | 188.0 | 189.4 | 292.7 | 231.7 | 20.8 % | 4776 | 30911 | 1.5 | 184.0 |

![Ruta de ejemplo](ruta_ejemplo.png)

## Cuellos de botella: Edmonds-Karp (Recepción → Despacho)

| Flujo máximo | Pasillos en el corte mínimo | Caminos de aumento | ms |
|---|---|---|---|
| 73 operarios/min | 45 | 53 | 25.0 |

Congestión de los pasillos del corte: {'Media': 20, 'Alta': 21, 'Baja': 4}. Columnas donde está el corte: {19: 45}.

![Cuellos de botella](cuellos_de_botella.png)
