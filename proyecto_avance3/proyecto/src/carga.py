"""Lectura y escritura de archivos. Nunca modifica el dataset original."""
from pathlib import Path
import pandas as pd

RUTAS_ORIGINAL = ["datos/originales/dataset.csv", "datos/dataset.csv"]


def localizar_original(raiz):
    """Busca el CSV original (ruta relativa a la raíz del proyecto)."""
    for rel in RUTAS_ORIGINAL:
        if (raiz / rel).exists():
            return raiz / rel
    return None


def cargar_datos(ruta):
    """Carga el CSV (sep ';', latin-1, decimal ',') y avisa si se omitieron líneas."""
    try:
        datos = pd.read_csv(ruta, sep=";", encoding="latin-1", decimal=",", on_bad_lines="skip")
    except Exception as e:
        print(f"Error al cargar '{ruta}': {e}")
        return None
    # on_bad_lines='skip' descarta líneas mal formadas sin avisar: se compara con el total de líneas.
    with open(ruta, "rb") as f:
        lineas = sum(1 for _ in f) - 1
    omitidas = lineas - len(datos)
    if omitidas > 0:
        print(f"ADVERTENCIA: ~{omitidas:,} líneas del archivo no se cargaron (líneas mal formadas "
              f"o saltos de línea dentro de campos).")
    return datos


def inspeccionar_datos(datos):
    """Inspección inicial (Avance 1)."""
    if datos is None:
        print("No hay datos para inspeccionar.")
        return
    print("\n=== DIMENSIONES ===")
    print(f"Filas: {datos.shape[0]:,} | Columnas: {datos.shape[1]}")
    print("\n=== TIPOS DE DATOS ===")
    print(datos.dtypes)
    print("\n=== PRIMEROS 5 REGISTROS ===")
    print(datos.head())


def guardar_datos(df, ruta, muestra_filas=1000):
    """Guarda el dataset procesado (UTF-8, ',') y una muestra aleatoria liviana para el repositorio."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta, index=False, encoding="utf-8")
    muestra = ruta.with_name(ruta.stem + "_muestra.csv")
    # muestra aleatoria reproducible (cubre todos los años y regiones, a diferencia de df.head)
    df.sample(n=min(muestra_filas, len(df)), random_state=42).sort_index().to_csv(
        muestra, index=False, encoding="utf-8")
    return ruta, muestra
