"""Estadística descriptiva (Avance 3, actividad A) y verificación de cálculos."""
import numpy as np
import pandas as pd

from src.validaciones import MESES, presentes

VARIABLES_NUMERICAS = MESES + ["total_anual", "pct_verano", "n_meses_imputados"]
VARIABLES_CATEGORICAS = ["anio", "region_origen", "region_destino", "mes_pico",
                         "nivel_flujo", "es_intrarregional"]
COLUMNAS_CSV = ["tipo", "variable", "categoria", "n_registros", "n_nulos", "media", "mediana",
                "minimo", "maximo", "rango", "desv_estandar", "q1", "q3", "cv_pct", "pct_ceros",
                "frecuencia", "porcentaje"]


def estadisticas_numericas(df):
    """Una fila por variable numérica: n, media, mediana, mín, máx, rango, desv., cuartiles."""
    filas = []
    for c in presentes(df, VARIABLES_NUMERICAS):
        s = pd.to_numeric(df[c], errors="coerce").dropna()
        media = s.mean()
        filas.append({
            "tipo": "numerica", "variable": c, "categoria": "",
            "n_registros": len(s), "n_nulos": int(df[c].isna().sum()),
            "media": media, "mediana": s.median(), "minimo": s.min(), "maximo": s.max(),
            "rango": s.max() - s.min(), "desv_estandar": s.std(),
            "q1": s.quantile(0.25), "q3": s.quantile(0.75),
            "cv_pct": s.std() / media * 100 if media else np.nan,
            "pct_ceros": (s == 0).mean() * 100 if len(s) else np.nan})
    return pd.DataFrame(filas)


def frecuencias_categoricas(df, top=20):
    """Frecuencia absoluta y relativa de cada categoría (las regiones, hasta `top`)."""
    filas = []
    for c in presentes(df, VARIABLES_CATEGORICAS):
        vc = df[c].value_counts(dropna=False)
        vc = vc[vc > 0]
        if c == "anio" or c == "es_intrarregional":
            vc = vc.sort_index()
        elif c == "mes_pico":
            vc = vc.reindex([m for m in MESES + ["sin flujo"] if m in vc.index])
        else:
            vc = vc.head(top)
        for cat, n in vc.items():
            filas.append({"tipo": "categorica", "variable": c, "categoria": str(cat),
                          "frecuencia": int(n), "porcentaje": n / len(df) * 100})
    return pd.DataFrame(filas)


def calcular_estadisticas(df):
    """Devuelve (tabla_para_csv, tabla_numerica, tabla_frecuencias)."""
    num, frec = estadisticas_numericas(df), frecuencias_categoricas(df)
    todo = pd.concat([num, frec], ignore_index=True)
    return todo.reindex(columns=COLUMNAS_CSV).round(4), num, frec


def verificar_calculos(df, num, anuales, estac):
    """Comprobaciones cruzadas independientes. Devuelve lista de (nombre, ok, detalle)."""
    res = []
    tot = float(df["total_anual"].sum())

    # 1) media y mediana de la tabla vs. cálculo directo con NumPy
    v = df["total_anual"].to_numpy(dtype=float)
    f = num[num["variable"] == "total_anual"].iloc[0]
    ok = np.isclose(f["media"], np.nanmean(v)) and np.isclose(f["mediana"], np.nanmedian(v))
    res.append(("Media y mediana de total_anual coinciden con NumPy", bool(ok),
                f"media {f['media']:.4f} vs {np.nanmean(v):.4f}"))

    # 2) suma por año = suma total
    res.append(("Suma de totales anuales = total general",
                bool(np.isclose(anuales.sum(), tot)), f"{anuales.sum():,.2f} vs {tot:,.2f}"))

    # 3) suma por región destino (incluye 'desconocido') = suma total
    por_region = float(df.groupby("region_destino", observed=True)["total_anual"].sum().sum())
    res.append(("Suma por región destino = total general",
                bool(np.isclose(por_region, tot)), f"{por_region:,.2f} vs {tot:,.2f}"))

    # 4) los 12 meses suman total_anual en cada fila
    meses = presentes(df, MESES)
    dif = float((df[meses].sum(axis=1) - df["total_anual"]).abs().max())
    res.append(("En cada fila, suma de meses = total_anual", dif < 0.02, f"diferencia máx. {dif:.4f}"))

    # 5) pct_verano dentro de 0-100 y coherente con los meses
    if "pct_verano" in df.columns:
        pv = df["pct_verano"]
        res.append(("pct_verano entre 0 y 100", bool(pv.between(0, 100).all()),
                    f"mín {pv.min():.2f} / máx {pv.max():.2f}"))

    # 6) los porcentajes mensuales de cada región suman 100
    if len(estac):
        s = estac[[f"pct_{m}" for m in MESES]].sum(axis=1)
        res.append(("Porcentajes mensuales por región suman 100",
                    bool(np.allclose(s, 100)), f"mín {s.min():.4f} / máx {s.max():.4f}"))

    # 7) las frecuencias de una variable sin nulos suman el total de filas
    n = int(df["anio"].value_counts().sum())
    res.append(("Frecuencias por año suman el total de filas", n == len(df), f"{n:,} vs {len(df):,}"))
    return res
