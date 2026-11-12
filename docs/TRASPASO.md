# Traspaso: estado de la rama `hito2` al 12/11/2026

> Resumen para continuar el trabajo en otra sesión (por ejemplo, en local). Lo escribió Claude al cerrar una sesión en la nube. Cuando ya no haga falta, se puede borrar.

## Para empezar en local

```bash
git fetch origin
git switch hito2 && git pull          # debe quedar en el commit «docs: add handoff notes» o posterior
pip install -r requirements.txt
python -m pytest                      # 82 pruebas, deben pasar todas
python scripts/app.py                 # la ventana
```

Todo lo hecho en la nube está subido; no quedó nada sin subir.

## Qué pide el hito 2 (entrega: domingo 22/11/2026, 23:59 · 0 a 5 puntos)

Se entrega **el informe** (4 a 10 páginas), no el código. Secciones: descripción del problema, dataset, propuesta final y **diseño del aplicativo**. Archivo: `TB2_1ACC0184_2026-20_CodigoAlum_ApellidoAlum`. El aplicativo con GUI, la validación de resultados, el video y el zip son del hito 3 (29/11).

El enunciado, la rúbrica y el borrador del informe están en el repo privado del curso (`yhocz-upc/1acc0184-complejidad-algoritmica`):
- enunciado: `06 - Evaluación_2026-20/TB1 - Trabajo Parcial/Recursos/TB1_1ACC0184_2026-20_Enunciado/README.md`
- borrador del informe: `trabajos/kivaflow/tb2-hito2/README.md`

## Lo que se hizo en esta rama (commits del 09 al 12/11)

| Commit | Qué |
|---|---|
| `3962737` | Imágenes del README movidas a `docs/image/` |
| `f46b089` | `carrera.py --guardar` crea `resultados/` si no existe |
| `0d31fdf` | **Orden de visita óptimo** (Held-Karp, `kivaflow/orden.py`), botón «Orden: voraz vs óptimo», casilla «Ver congestión», `scripts/experimento.py` (160 pedidos) |
| `1c33aa3` | README: orden óptimo, tabla del experimento, qué hace falta para ejecutarlo |
| `b11ecb1` | **Ventana rediseñada** (`kivaflow/interfaz.py`): cabecera, tarjetas, botones por tipo y tabla comparativa con conclusión |
| `ee62a89` | `scripts/diagramas.py`: diagramas con Graphviz (`docs/image/arquitectura.png`, `flujo_pedido.png`, `sector_mst.png`) y `data/sector_picking.in` en el formato `vecino|peso` del cuaderno de Kruskal del profe |

## Lo que falta

### 1. Actualizar el borrador del informe (lo más importante: es lo que se entrega)

El borrador (`trabajos/kivaflow/tb2-hito2/README.md`, repo del curso) quedó atrás del código:

- **Sección 2.1 (origen del dataset):** dice que el generador usa NetworkX, NumPy y pandas. El código de esta rama usa solo la librería estándar (`csv`, `random`); NetworkX solo aparece en las pruebas. Hay que corregirlo, porque el profe puede auditar el código.
- **Sección 3 (propuesta):** no menciona el orden óptimo con Held-Karp (entra en «Programación Dinámica y Algoritmos Voraces», técnica aceptada) ni el experimento. Números listos en el README de esta rama: Bellman-Ford ahorra ~19 % de caminata frente a BFS; el orden óptimo ahorra hasta 9,4 % más con 8 productos. Referencia: Held y Karp (1962), ya está en el README.
- **Sección 4 (diseño del aplicativo):** no tiene ningún diagrama ni captura. Agregar `docs/image/arquitectura.png`, `docs/image/flujo_pedido.png` y `docs/image/app.png`. Actualizar los requisitos funcionales (orden voraz/óptimo, ver congestión, medición de tiempo/memoria/operaciones).
- **Datos viejos:** dice «27 pruebas» (son 82) y que la GUI queda para el hito 3 (ya hay ventana).
- **Carátula:** faltan nombres y códigos de los otros dos integrantes (están en el Word del TB1).
- **Bitácora de IA (anexo):** agregar filas para lo hecho del 09 al 12/11 (orden óptimo, experimento, rediseño de la ventana, diagramas).
- **Extensión:** verificar que no pase de 10 páginas al pasarlo al Word o Google Docs.

### 2. Probar la ventana en Windows

El rediseño solo se probó generando capturas en Linux (sin abrir ventana). Falta abrir `python scripts/app.py` en la PC y revisar que nada se vea descuadrado ni con textos cortados, y probar los clics en el mapa y los botones «Carrera…».

### 3. Decidir sobre Instacart (opcional)

El README lo marca como «falta correrlo con los datos de Kaggle». Pasos: descargar `order_products__prior.csv` de la competencia *Instacart Market Basket Analysis*, ponerlo en `instacart/` y ejecutar `python scripts/generar_dataset.py --instacart instacart`.

Ojo: eso cambia la congestión de todos los pasillos, así que habría que regenerar las figuras de `resultados/` y **todos** los números del README y del informe (73 operarios/min, 2448,78 m, la tabla del experimento, etc.) y ajustar las pruebas que fijan esos valores (`tests/test_app.py`). Recomendación: quedarse con el dataset sintético, que el profe ya aceptó en el TB1 (19/20).

### 4. Cosas menores

- Para regenerar los diagramas hace falta Graphviz instalado (`pip install graphviz` + https://graphviz.org/download/). Las imágenes ya están en `docs/image/`, así que no es obligatorio.
- La mochila 0/1 y Floyd-Warshall siguen solo en `scripts/demo.py`, no en la ventana.
- `scripts/carrera.py` y `scripts/analisis.py` conservan el estilo anterior; se les puede aplicar `interfaz.aplicar_tema`.
- `scripts/experimento.py` tarda unos 4 minutos (`--pedidos 10` para probar).

## Otras ramas

- `claude/redesign-similar-solutions-8kmlm9`: rediseño oscuro de la **app web** (Streamlit, parte de `main`), commit `b20e321`. Está subido pero **sin unir** a `main`; es para el hito 3. Para unirlo: revisar y hacer merge (o PR) hacia `main`, que es de donde sale la app publicada.
- `main` y `tb2`: sin cambios en esta sesión.
