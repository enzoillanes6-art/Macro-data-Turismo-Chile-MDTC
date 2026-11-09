"""Normalización, corrección de rangos, duplicados y tratamiento de nulos."""
import unicodedata
import pandas as pd

from src import validaciones as val
from src.reporte import registrar

def _sin_tildes(texto):
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def _eliminar(df, mascara, motivo, registro):
    n = int(mascara.sum())
    if n:
        registrar(registro, "eliminaciones", motivo=motivo, filas=n)
        df = df.loc[~mascara].copy()
    return df


# ---------------------------------------------------------------- LIMPIEZA
def normalizar_nombres_columnas(df, registro):
    nuevos = [val.normalizar_nombre(c) for c in df.columns]
    registro["mapeo_columnas"] = dict(zip(df.columns, nuevos))
    df.columns = nuevos
    return df


def limpiar_espacios(df, registro):
    """Quita espacios al inicio/fin, colapsa espacios dobles y convierte '' en nulo."""
    for c in df.columns:
        if pd.api.types.is_numeric_dtype(df[c]):
            continue
        original = df[c].astype("string")
        limpio = original.str.strip().str.replace(r"\s+", " ", regex=True).replace("", pd.NA)
        cambios = int((limpio.fillna("\0") != original.fillna("\0")).sum())
        if cambios:
            registrar(registro, "correcciones", accion=f"Espacios sobrantes / vacíos en '{c}'",
                      afectados=cambios)
        df[c] = limpio
    return df


def unificar_categorias(df, registro):
    """Variantes de mayúsculas/tildes de un mismo texto -> la variante más frecuente."""
    for c in val.presentes(df, val.COLUMNAS_NOMBRE):
        s = df[c]
        frecuencia = s.value_counts()
        grupos = {}
        for valor in frecuencia.index:                      # ordenado de más a menos frecuente
            clave = _sin_tildes(str(valor)).lower()
            grupos.setdefault(clave, valor)                  # la primera = la más frecuente
        mapa = {v: grupos[_sin_tildes(str(v)).lower()] for v in frecuencia.index}
        nuevo = s.map(mapa)
        cambios = int((nuevo.fillna("\0") != s.fillna("\0")).sum())
        if cambios:
            registrar(registro, "correcciones",
                      accion=f"Categorías inconsistentes unificadas en '{c}'", afectados=cambios)
        df[c] = nuevo
    return df


def corregir_fuera_de_rango(df, registro):
    # 1) valores no numéricos en columnas numéricas -> nulo
    for c in val.presentes(df, ["anio"] + val.COLUMNAS_CODIGO + val.MESES):
        if not pd.api.types.is_numeric_dtype(df[c]):
            conv = pd.to_numeric(df[c], errors="coerce")
            n = int(conv.isna().sum() - df[c].isna().sum())
            if n:
                registrar(registro, "correcciones",
                          accion=f"Valores no numéricos en '{c}' convertidos a nulo", afectados=n)
            df[c] = conv
    # 2) flujos negativos son imposibles -> nulo (se tratan en la etapa de nulos)
    for c in val.presentes(df, val.MESES):
        m = val._mascara_fuera(df[c], *val.RANGOS[c])
        if m.any():
            registrar(registro, "correcciones",
                      accion=f"Flujo negativo en '{c}' convertido a nulo", afectados=int(m.sum()))
            df.loc[m, c] = pd.NA
            df[c] = df[c].astype("float64")
    # 3) códigos de región fuera de 1-16 -> nulo (se recuperan desde el nombre)
    for c in val.presentes(df, ["cut_region_origen", "cut_region_destino"]):
        m = val._mascara_fuera(df[c], *val.RANGOS[c])
        if m.any():
            registrar(registro, "correcciones",
                      accion=f"Código de región fuera de 1-16 en '{c}' convertido a nulo",
                      afectados=int(m.sum()))
            df.loc[m, c] = pd.NA
    # 4) año fuera del período del estudio -> se elimina la fila
    if "anio" in df.columns:
        m = val._mascara_fuera(df["anio"], *val.RANGOS["anio"])
        df = _eliminar(df, m, "Año fuera del período 2018-2025", registro)
    return df


def eliminar_duplicados(df, registro):
    return _eliminar(df, df.duplicated(), "Fila duplicada exacta (se conserva la primera)", registro)


def revisar_ids_repetidos(df, registro):
    """Solo se informa: dos filas con mismo origen-destino-año pueden ser registros distintos."""
    n = val.contar_ids_repetidos(df)
    if n:
        registrar(registro, "correcciones",
                  accion="Identificadores origen-destino-año repetidos (revisados, NO modificados)",
                  afectados=n)
    return n


# ------------------------------------------------------------------- NULOS
def _recuperar_par(df, cod, nom):
    """Completa nombre desde código y código desde nombre usando el par más frecuente."""
    pares = (df.dropna(subset=[cod, nom]).groupby([cod, nom]).size().reset_index(name="n")
             .sort_values("n", ascending=False))
    cod2nom = pares.drop_duplicates(cod).set_index(cod)[nom]
    nom2cod = pares.drop_duplicates(nom).set_index(nom)[cod]
    m = df[nom].isna() & df[cod].notna()
    df.loc[m, nom] = df.loc[m, cod].map(cod2nom)
    m = df[cod].isna() & df[nom].notna()
    df.loc[m, cod] = df.loc[m, nom].map(nom2cod)
    return df


def tratar_nulos(df, registro):
    """Estrategia diferenciada por variable (ver justificaciones en el registro)."""
    # a) año: sin él el registro no se puede ubicar en el tiempo
    if "anio" in df.columns and df["anio"].isna().any():
        df = _eliminar(df, df["anio"].isna(), "Año nulo (registro no ubicable en el tiempo)", registro)
    if "anio" in df.columns:
        registrar(registro, "nulos", variable="anio", estrategia="Eliminar registros",
                  justificacion="Sin año no se puede analizar tendencia ni estacionalidad")

    # b) territorio: recuperar desde la otra columna del par; si no, 'desconocido' o eliminar
    pares = [("cut_comuna_origen", "comuna_origen"), ("cut_region_origen", "region_origen"),
             ("cut_comuna_destino", "comuna_destino"), ("cut_region_destino", "region_destino")]
    for cod, nom in pares:
        if cod not in df.columns or nom not in df.columns:
            continue
        df = _recuperar_par(df, cod, nom)
        df = _eliminar(df, df[cod].isna(), f"Sin código ni nombre recuperable en '{cod}'", registro)
        df[nom] = df[nom].fillna("desconocido")
        registrar(registro, "nulos", variable=cod, estrategia="Recuperar desde nombre; si no, eliminar",
                  justificacion="El código CUT es identificador: el nombre asociado permite recuperarlo")
        registrar(registro, "nulos", variable=nom, estrategia="Recuperar desde código; si no, 'desconocido'",
                  justificacion="El código CUT determina el nombre oficial; el resto no se inventa")

    # c) meses: fila sin ningún mes no aporta información; el resto, 0 con marca
    meses = val.presentes(df, val.MESES)
    if meses:
        df = _eliminar(df, df[meses].isna().all(axis=1),
                       "Fila sin ningún dato de flujo mensual", registro)
        df["n_meses_imputados"] = df[meses].isna().sum(axis=1).astype("int8")
        df[meses] = df[meses].fillna(0)
        for m in meses:
            registrar(registro, "nulos", variable=m,
                      estrategia="Imputar 0 (solo si la fila tiene otros meses) + marca n_meses_imputados",
                      justificacion="En una matriz origen-destino un mes sin registro equivale a flujo "
                                    "no observado; la marca permite excluirlos si se requiere")

    # d) cualquier otra columna con nulos: mediana (numérica) o 'desconocido' (texto)
    conocidas = set(val.COLUMNAS_REQUERIDAS) | {"n_meses_imputados"}
    for c in df.columns:
        if c in conocidas or not df[c].isna().any():
            continue
        if pd.api.types.is_numeric_dtype(df[c]):
            df[c] = df[c].fillna(df[c].median())
            registrar(registro, "nulos", variable=c, estrategia="Imputar con la mediana",
                      justificacion="Robusta a valores extremos, frecuentes en datos de flujo")
        else:
            df[c] = df[c].fillna("desconocido")
            registrar(registro, "nulos", variable=c, estrategia="Categoría 'desconocido'",
                      justificacion="Variable categórica: no se infiere un valor sin fuente")
    return df
