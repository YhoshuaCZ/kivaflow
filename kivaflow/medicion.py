"""Cómo se mide la eficiencia de un algoritmo en KivaFlow.

Para cada ejecución se guardan tres medidas:

- **Tiempo** (velocidad): `time.perf_counter`, el mejor de varias repeticiones.
  Se toma el mínimo porque las demás solo suman ruido del sistema operativo.
- **Memoria** (espacio): el pico de memoria que reservó el algoritmo mientras
  corría, con `tracemalloc`. Se mide en una corrida aparte, porque `tracemalloc`
  hace más lento el programa y ensuciaría el tiempo.
- **Operaciones**: lo que cuenta cada algoritmo (nodos visitados, arcos revisados,
  relajaciones, caminos de aumento…). No depende de la computadora, así que es
  lo que se compara con la complejidad teórica (O grande).
"""
import csv
import time
import tracemalloc
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Medicion:
    tarea: str  # «ruta del pedido», «flujo máximo», «red de servicio»…
    algoritmo: str
    complejidad: str  # la teórica, por ejemplo «O(V + E)»
    ms: float
    pico_kb: float
    operaciones: dict = field(default_factory=dict)
    resultado: dict = field(default_factory=dict)


def medir(funcion, *args, repeticiones=3, **kwargs):
    """Ejecuta `funcion` y devuelve (resultado, ms, pico_kb)."""
    tiempos = []
    for _ in range(repeticiones):
        t0 = time.perf_counter()
        resultado = funcion(*args, **kwargs)
        tiempos.append((time.perf_counter() - t0) * 1000)
    tracemalloc.start()
    funcion(*args, **kwargs)
    _, pico = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return resultado, min(tiempos), pico / 1024


def tabla(mediciones):
    """Las mediciones como texto alineado, para la consola y para la ventana."""
    filas = [f"{'Algoritmo':<22}{'Complejidad':<13}{'Tiempo':>10}{'Memoria':>11}"]
    filas.append("-" * len(filas[0]))
    for m in mediciones:
        filas.append(f"{m.algoritmo:<22}{m.complejidad:<13}{m.ms:>8.1f}ms{m.pico_kb:>8.0f} KB")
        for k, v in m.operaciones.items():
            filas.append(f"    {k}: {v:,}".replace(",", " "))
        for k, v in m.resultado.items():
            filas.append(f"    {k}: {v}")
    return "\n".join(filas)


def guardar_csv(mediciones, ruta, extra=None):
    """Agrega una fila por medición a un CSV (lo crea con encabezado si no existe)."""
    nuevo = not ruta.exists()
    ruta.parent.mkdir(exist_ok=True)
    with open(ruta, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["Fecha", "Tarea", "Algoritmo", "Complejidad", "Tiempo_ms", "Memoria_pico_KB",
                        "Operaciones", "Resultado", "Detalle"])
        ahora = datetime.now().isoformat(timespec="seconds")
        for m in mediciones:
            w.writerow([ahora, m.tarea, m.algoritmo, m.complejidad, f"{m.ms:.2f}", f"{m.pico_kb:.1f}",
                        "; ".join(f"{k}={v}" for k, v in m.operaciones.items()),
                        "; ".join(f"{k}={v}" for k, v in m.resultado.items()), extra or ""])
