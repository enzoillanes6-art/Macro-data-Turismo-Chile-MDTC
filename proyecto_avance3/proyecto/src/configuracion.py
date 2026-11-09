"""Rutas, constantes y utilidades compartidas por el Avance 3."""
import re
from pathlib import Path

import pandas as pd

from src.validaciones import MESES

RAIZ = Path(__file__).resolve().parent.parent
RUTA_LIMPIO = RAIZ / "datos" / "procesados" / "dataset_limpio.csv"
RUTA_MUESTRA = RAIZ / "datos" / "procesados" / "dataset_limpio_muestra.csv"
DIR_RESULTADOS = RAIZ / "resultados"
DIR_GRAFICOS = DIR_RESULTADOS / "graficos"
RUTA_ESTADISTICAS = DIR_RESULTADOS / "estadisticas.csv"
RUTA_INDICADORES = DIR_RESULTADOS / "indicadores.csv"
RUTA_ESTACIONALIDAD = DIR_RESULTADOS / "estacionalidad_regional.csv"
RUTA_INFORME = RAIZ / "reportes" / "avance_3.pdf"
RUTA_LOG = RAIZ / "reportes" / "ejecucion_avance3.txt"
RUTA_RESPUESTAS = RAIZ / "reportes" / "respuestas_finales.md"   # texto editable por el equipo

URL_REPOSITORIO = "https://github.com/BenjaAgx/Macro-data-Turismo-Chile-MDTC-"
UNIDAD = "viajes turísticos"          # unidad de la matriz origen-destino (ajustar si corresponde)
VERANO = ["diciembre", "enero", "febrero"]
MESES_CORTOS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
COLUMNAS_CATEGORICAS = ["comuna_origen", "region_origen", "comuna_destino", "region_destino",
                        "mes_pico", "nivel_flujo"]
COLUMNAS_REQUERIDAS = ["anio", "total_anual", "region_origen", "region_destino"] + MESES


def fmt(x, dec=None):
    """Formato chileno: 1.234.567,8. Sin 'dec' elige los decimales según la magnitud."""
    if x is None or pd.isna(x):
        return "-"
    if dec is None:
        a = abs(x)
        dec = 0 if a >= 1000 else (1 if a >= 100 else 2)
    s = f"{x:,.{dec}f}"
    return s.replace(",", "\0").replace(".", ",").replace("\0", ".")


def pct(x, dec=1):
    return fmt(x, dec) + "%"


def nombre_corto(region):
    """'Región de Los Lagos' -> 'Los Lagos' (para ejes y leyendas)."""
    r = re.sub(r"^Regi[oó]n\s+(?:del?\s+(?:la\s+)?)?", "", str(region).strip(), flags=re.I)
    base = r.lower()
    for inicio, corto in (("metropolitana", "Metropolitana"), ("ays", "Aysén"), ("magallanes", "Magallanes"),
                          ("libertador", "O'Higgins"), ("o'higgins", "O'Higgins"), ("ohiggins", "O'Higgins")):
        if base.startswith(inicio):
            return corto
    return r if r else str(region)


def cargar_limpio():
    """Lee el dataset limpio del Avance 2. Devuelve (DataFrame, ruta usada).

    Si el archivo completo no está (pesa >100 MB y no se sube a GitHub), usa la muestra.
    """
    ruta = RUTA_LIMPIO if RUTA_LIMPIO.exists() else RUTA_MUESTRA
    if not ruta.exists():
        raise FileNotFoundError(
            "No existe datos/procesados/dataset_limpio.csv. Ejecuta primero el pipeline del "
            "Avance 2 (coloca dataset.csv en datos/originales/ y corre python main.py).")
    if ruta == RUTA_MUESTRA:
        print("AVISO: no existe dataset_limpio.csv completo; se usa la muestra "
              "(dataset_limpio_muestra.csv). Los resultados son solo referenciales.")
    cab = pd.read_csv(ruta, nrows=0, encoding="utf-8").columns
    faltan = [c for c in COLUMNAS_REQUERIDAS if c not in cab]
    if faltan:
        raise ValueError(f"Al dataset limpio le faltan columnas requeridas: {faltan}")
    dtype = {c: "category" for c in COLUMNAS_CATEGORICAS if c in cab}
    usar = [c for c in cab if c != "fecha_periodo"]
    df = pd.read_csv(ruta, usecols=usar, dtype=dtype, encoding="utf-8")
    return df, ruta
