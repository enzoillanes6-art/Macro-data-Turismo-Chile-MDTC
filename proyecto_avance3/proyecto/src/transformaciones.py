"""Conversión de tipos y creación de variables."""
import numpy as np
import pandas as pd

from src import validaciones as val
from src.reporte import registrar


def convertir_tipos(df, registro):
    """Tipos finales: enteros compactos para códigos/año y 'category' para nombres."""
    if "anio" in df.columns:
        df["anio"] = df["anio"].astype("int16")
        registrar(registro, "transformaciones", original="anio", transformacion="Conversión a entero",
                  resultado="Año como entero compacto", tipo_final="int16")
    for c in val.presentes(df, val.COLUMNAS_CODIGO):
        df[c] = df[c].astype("int32")
    registrar(registro, "transformaciones", original=", ".join(val.presentes(df, val.COLUMNAS_CODIGO)),
              transformacion="Conversión a entero", resultado="Códigos CUT enteros", tipo_final="int32")
    for c in val.presentes(df, val.MESES):
        df[c] = pd.to_numeric(df[c], errors="coerce").astype("float64")
    registrar(registro, "transformaciones", original="enero ... diciembre",
              transformacion="Conversión numérica (pd.to_numeric)", resultado="Flujos mensuales numéricos",
              tipo_final="float64")
    for c in val.presentes(df, val.COLUMNAS_NOMBRE):
        df[c] = df[c].astype("category")
    registrar(registro, "transformaciones", original="nombres de comuna y región",
              transformacion="Normalización de categorías (texto limpio + category)",
              resultado="Nombres únicos por categoría", tipo_final="category")
    return df


def crear_fecha(df, registro):
    if "anio" in df.columns:
        df["fecha_periodo"] = pd.to_datetime(df["anio"].astype(str), format="%Y")
        registrar(registro, "transformaciones", original="anio", transformacion="pd.to_datetime",
                  resultado="fecha_periodo = 1 de enero del año", tipo_final="datetime64[ns]")
    return df


def crear_total_anual(df, registro):
    meses = val.presentes(df, val.MESES)
    df["total_anual"] = df[meses].sum(axis=1).round(2)
    registrar(registro, "transformaciones", original="enero ... diciembre",
              transformacion="Nueva variable: suma de los 12 meses",
              resultado="total_anual", tipo_final="float64")
    return df


def crear_mes_pico(df, registro):
    meses = val.presentes(df, val.MESES)
    pico = df[meses].idxmax(axis=1)
    df["mes_pico"] = pico.where(df["total_anual"] > 0, "sin flujo").astype("category")
    registrar(registro, "transformaciones", original="enero ... diciembre",
              transformacion="Nueva variable: mes con mayor flujo", resultado="mes_pico",
              tipo_final="category")
    return df


def crear_porcentaje_verano(df, registro):
    verano = val.presentes(df, ["diciembre", "enero", "febrero"])
    df["pct_verano"] = np.where(df["total_anual"] > 0,
                                df[verano].sum(axis=1) / df["total_anual"].where(df["total_anual"] > 0) * 100,
                                0.0).round(2)
    registrar(registro, "transformaciones", original="diciembre, enero, febrero, total_anual",
              transformacion="Nueva variable: % del flujo anual en verano (dic-feb)",
              resultado="pct_verano (0-100)", tipo_final="float64")
    return df


def crear_intrarregional(df, registro):
    if {"cut_region_origen", "cut_region_destino"} <= set(df.columns):
        df["es_intrarregional"] = (df["cut_region_origen"] == df["cut_region_destino"]).astype("int8")
        registrar(registro, "transformaciones", original="cut_region_origen, cut_region_destino",
                  transformacion="Nueva variable binaria: viaje dentro de la misma región",
                  resultado="es_intrarregional (1 = sí)", tipo_final="int8")
    return df


def clasificar_nivel_flujo(df, registro):
    """sin flujo / bajo / medio / alto (terciles del total anual con flujo > 0)."""
    positivo = df["total_anual"] > 0
    nivel = pd.Series("sin flujo", index=df.index, dtype="object")
    if positivo.sum() >= 3:
        nivel[positivo] = pd.qcut(df.loc[positivo, "total_anual"], 3,
                                  labels=["bajo", "medio", "alto"], duplicates="drop").astype(str)
    df["nivel_flujo"] = nivel.astype("category")
    registrar(registro, "transformaciones", original="total_anual",
              transformacion="Clasificación por rangos (terciles de flujo > 0)",
              resultado="nivel_flujo: sin flujo / bajo / medio / alto", tipo_final="category")
    return df
