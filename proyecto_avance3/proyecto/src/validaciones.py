"""Diagnóstico y validación de columnas, tipos y rangos."""
import re
import unicodedata

import pandas as pd

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]

COLUMNAS_CODIGO = ["cut_comuna_origen", "cut_region_origen",
                   "cut_comuna_destino", "cut_region_destino"]
COLUMNAS_NOMBRE = ["comuna_origen", "region_origen", "comuna_destino", "region_destino"]
COLUMNAS_REQUERIDAS = COLUMNAS_CODIGO + COLUMNAS_NOMBRE + ["anio"] + MESES
CLAVE_REGISTRO = ["cut_comuna_origen", "cut_comuna_destino", "anio"]

# (mínimo, máximo) permitidos; None = sin límite
RANGOS = {"anio": (2018, 2025),
          "cut_region_origen": (1, 16),
          "cut_region_destino": (1, 16),
          **{m: (0, None) for m in MESES}}


ALIAS = {"ano": "anio"}


def normalizar_nombre(nombre):
    """'Año' -> 'anio', 'CUT Región Origen' -> 'cut_region_origen'."""
    sin = "".join(c for c in unicodedata.normalize("NFKD", str(nombre)) if not unicodedata.combining(c))
    n = re.sub(r"[^a-z0-9]+", "_", sin.strip().lower()).strip("_")
    return ALIAS.get(n, n)


def presentes(df, columnas):
    return [c for c in columnas if c in df.columns]


def _mascara_fuera(serie, minimo, maximo):
    x = pd.to_numeric(serie, errors="coerce")
    m = pd.Series(False, index=serie.index)
    if minimo is not None:
        m |= x < minimo
    if maximo is not None:
        m |= x > maximo
    return m


def contar_fuera_de_rango(df):
    """Cantidad de valores fuera de rango por columna (ignora nulos)."""
    return {c: int(_mascara_fuera(df[c], *RANGOS[c]).sum()) for c in presentes(df, RANGOS)}


def contar_ids_repetidos(df):
    claves = presentes(df, CLAVE_REGISTRO)
    if len(claves) < len(CLAVE_REGISTRO):
        return 0
    return int(df.duplicated(subset=claves).sum())


def diagnosticar(df):
    nulos = df.isna().sum()
    vista = df.rename(columns=normalizar_nombre)   # permite diagnosticar antes de normalizar
    fuera = contar_fuera_de_rango(vista)
    return {
        "filas": int(df.shape[0]),
        "columnas": int(df.shape[1]),
        "dtypes": {c: str(t) for c, t in df.dtypes.items()},
        "nulos": nulos,
        "pct_nulos": nulos / max(len(df), 1) * 100,
        "nulos_total": int(nulos.sum()),
        "duplicados": int(df.duplicated().sum()),
        "ids_repetidos": contar_ids_repetidos(vista),
        "fuera_rango": fuera,
        "fuera_rango_total": int(sum(fuera.values())),
    }


def imprimir_diagnostico(d, titulo):
    print(f"\n--- {titulo} ---")
    print(f"Filas: {d['filas']:,} | Columnas: {d['columnas']}")
    print(f"Nulos totales: {d['nulos_total']:,} | Duplicados exactos: {d['duplicados']:,} | "
          f"Ids repetidos: {d['ids_repetidos']:,} | Fuera de rango: {d['fuera_rango_total']:,}")
    con_nulos = d["nulos"][d["nulos"] > 0]
    if len(con_nulos):
        print("Nulos por columna (cantidad / %):")
        for c, n in con_nulos.items():
            print(f"  {c}: {n:,} ({d['pct_nulos'][c]:.3f}%)")
    for c, n in d["fuera_rango"].items():
        if n:
            print(f"  fuera de rango en {c}: {n:,}")


def validar(df):
    """Devuelve lista de (nombre, ok, detalle)."""
    res = []
    faltan = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
    res.append(("Columnas requeridas presentes", not faltan,
                "todas" if not faltan else f"faltan: {faltan}"))

    meses = presentes(df, MESES)
    no_num = [c for c in meses + presentes(df, ["anio"] + COLUMNAS_CODIGO)
              if not pd.api.types.is_numeric_dtype(df[c])]
    res.append(("Tipos numéricos en meses, año y códigos", not no_num,
                "correctos" if not no_num else f"no numéricas: {no_num}"))

    fuera = {k: v for k, v in contar_fuera_de_rango(df).items() if v}
    res.append(("Valores dentro de rango", not fuera, "sin fuera de rango" if not fuera else str(fuera)))

    clave = presentes(df, COLUMNAS_CODIGO + COLUMNAS_NOMBRE + ["anio"] + meses)
    n_nulos = int(df[clave].isna().sum().sum()) if clave else 0
    res.append(("Sin nulos en identificadores ni meses", n_nulos == 0, f"{n_nulos} nulos"))

    dup = int(df.duplicated().sum())
    res.append(("Sin filas duplicadas", dup == 0, f"{dup} duplicadas"))

    if meses and "total_anual" in df.columns:
        dif = float((df[meses].sum(axis=1) - df["total_anual"]).abs().max()) if len(df) else 0.0
        res.append(("total_anual coincide con suma de meses", dif < 0.01, f"diferencia máx. {dif:.2e}"))
    return res
