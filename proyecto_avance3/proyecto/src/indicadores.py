"""Indicadores automatizados (Avance 3, actividad B) y tablas de apoyo."""
import numpy as np
import pandas as pd

from src.configuracion import UNIDAD, VERANO, fmt, nombre_corto, pct
from src.validaciones import MESES


# ------------------------------------------------------------------ TABLAS DE APOYO
def totales_anuales(df):
    """Total nacional de viajes por año (serie indexada por año)."""
    return df.groupby("anio")["total_anual"].sum().sort_index()


def totales_mensuales_nacional(df):
    """Total nacional de viajes por mes (serie indexada por nombre de mes)."""
    return df[MESES].sum()


def tabla_estacionalidad(df):
    """Estacionalidad por región destino (excluye la categoría 'desconocido').

    - pct_<mes>: % del flujo anual de la región que ocurre en ese mes.
    - pct_verano: % del flujo anual en dic-ene-feb (25% = reparto uniforme).
    - indice_estacionalidad: mes de mayor flujo / promedio mensual (1 = sin estacionalidad).
    - cv_mensual_pct: coeficiente de variación de los 12 meses.
    """
    g = df.groupby("region_destino", observed=True)[MESES].sum()
    g = g[~g.index.astype(str).str.lower().isin(["desconocido"])]
    g = g[g.sum(axis=1) > 0]
    tot = g.sum(axis=1)
    p = g.div(tot, axis=0) * 100
    res = pd.DataFrame({
        "region": [nombre_corto(r) for r in g.index],
        "region_original": g.index.astype(str),
        "viajes_totales": tot.to_numpy(),
        "pct_verano": p[VERANO].sum(axis=1).to_numpy(),
        "mes_pico": p.idxmax(axis=1).to_numpy(),
        "indice_estacionalidad": (g.max(axis=1) / g.mean(axis=1)).to_numpy(),
        "cv_mensual_pct": (g.std(axis=1, ddof=0) / g.mean(axis=1) * 100).to_numpy(),
    })
    for m in MESES:
        res[f"pct_{m}"] = p[m].to_numpy()
    return res.sort_values("viajes_totales", ascending=False).reset_index(drop=True)


def resumen_distribucion(df):
    """Datos de la distribución de total_anual entre registros con flujo (para gráfico 04)."""
    s = df["total_anual"]
    pos = s[s > 0]
    if pos.empty:
        return {}
    p99 = pos.quantile(0.99)
    return {"n_pos": len(pos), "mediana": pos.median(), "media": pos.mean(), "maximo": pos.max(),
            "p99": p99, "n_criticos": int((s > p99).sum()),
            "pct_viajes_criticos": s[s > p99].sum() / s.sum() * 100 if s.sum() else np.nan,
            "pct_menor_100": (pos < 100).mean() * 100, "pct_menor_1000": (pos < 1000).mean() * 100}


# ------------------------------------------------------------------ INDICADORES
def _ind(nombre, metodo, resultado, interpretacion):
    return {"indicador": nombre, "metodo_calculo": metodo, "resultado": resultado,
            "interpretacion": interpretacion}


def calcular_indicadores(df, anuales, estac, dist):
    """Devuelve la tabla indicador / método / resultado / interpretación (12 indicadores)."""
    out, N, tot = [], len(df), float(df["total_anual"].sum())
    nat = totales_mensuales_nacional(df)

    # 1. Registros válidos
    validos = int((df["total_anual"].notna() & (df["total_anual"] >= 0)).sum())
    out.append(_ind("Total de registros válidos",
                    "Filas con total_anual no nulo y no negativo",
                    f"{fmt(validos, 0)} de {fmt(N, 0)} ({pct(validos / N * 100)})",
                    "Proporción del dataset limpio utilizable; cada registro es un par comuna "
                    "origen-destino en un año."))

    # 2. Registros sin flujo
    ceros = (df["total_anual"] == 0).mean() * 100
    out.append(_ind("% de registros sin flujo",
                    "Filas con total_anual = 0 sobre el total de filas",
                    pct(ceros),
                    "Pares origen-destino sin viajes registrados en el año. Un valor alto indica "
                    "una matriz dispersa: el flujo se concentra en pocas rutas."))

    # 3. Variación primer a último año
    if len(anuales) >= 2 and anuales.iloc[0] > 0:
        a0, a1 = anuales.index[0], anuales.index[-1]
        v0, v1 = anuales.iloc[0], anuales.iloc[-1]
        var = (v1 - v0) / v0 * 100
        cagr = ((v1 / v0) ** (1 / (a1 - a0)) - 1) * 100 if v1 > 0 else np.nan
        sentido = "creció" if var > 0 else "disminuyó"
        out.append(_ind(f"Variación del flujo total {a0} a {a1}",
                        "(Total último año - Total primer año) / Total primer año x 100",
                        f"{var:+.1f}% (tasa anual compuesta {cagr:+.1f}%)".replace(".", ","),
                        f"El flujo nacional {sentido} {fmt(abs(var), 1)}% entre {a0} y {a1}. "
                        "Resume la tendencia de largo plazo; los años intermedios se ven en el gráfico 01."))
        # 4. Último período
        b0, b1 = anuales.iloc[-2], anuales.iloc[-1]
        if b0 > 0:
            var2 = (b1 - b0) / b0 * 100
            out.append(_ind(f"Variación interanual {anuales.index[-2]} a {anuales.index[-1]}",
                            "(Total último año - Total año anterior) / Total año anterior x 100",
                            f"{var2:+.1f}%".replace(".", ","),
                            "Mide el momento más reciente de la serie: " +
                            ("el turismo sigue creciendo." if var2 > 0 else "el turismo se contrajo.")))
    else:
        out.append(_ind("Variación del flujo total entre años", "Requiere al menos 2 años de datos",
                        "No calculable", "El dataset usado contiene un solo año."))

    # 5. Concentración estival nacional
    if nat.sum() > 0:
        est = nat[VERANO].sum() / nat.sum() * 100
        mpico = nat.idxmax()
        out.append(_ind("Concentración estival nacional (dic-feb)",
                        "Suma de diciembre, enero y febrero / suma de los 12 meses x 100",
                        pct(est),
                        f"Si el flujo fuera parejo, 3 de 12 meses concentrarían 25%. El resultado queda "
                        f"{fmt(abs(est - 25), 1)} puntos {'sobre' if est > 25 else 'bajo'} ese nivel; "
                        f"el mes de mayor flujo nacional es {mpico}."))

    # 6. Mes pico más frecuente
    mp = pd.Series(dtype=int)
    if "mes_pico" in df.columns:
        mp = df["mes_pico"].astype(str)
        mp = mp[mp != "sin flujo"].value_counts()
    if len(mp):
        out.append(_ind("Mes pico más frecuente",
                        "Moda de mes_pico entre registros con flujo",
                        f"{mp.index[0]} ({pct(mp.iloc[0] / mp.sum() * 100)} de los registros)",
                        "Mes en que más pares origen-destino alcanzan su máximo: refleja la "
                        "estacionalidad típica de un registro individual."))

    # 7-8. Regiones más y menos estacionales
    if len(estac) >= 2:
        hi = estac.loc[estac["indice_estacionalidad"].idxmax()]
        lo = estac.loc[estac["indice_estacionalidad"].idxmin()]
        met = "Mes de mayor flujo / promedio mensual, por región destino (1 = sin estacionalidad)"
        out.append(_ind("Región destino más estacional", met,
                        f"{hi['region']} (índice {fmt(hi['indice_estacionalidad'], 2)}, "
                        f"pico en {hi['mes_pico']})",
                        f"Su mes pico recibe {fmt(hi['indice_estacionalidad'], 2)} veces el flujo mensual "
                        "promedio: es la región con demanda más concentrada en el año."))
        out.append(_ind("Región destino menos estacional", met,
                        f"{lo['region']} (índice {fmt(lo['indice_estacionalidad'], 2)}, "
                        f"pico en {lo['mes_pico']})",
                        "Tiene el flujo mejor distribuido durante el año, lo que reduce la presión "
                        "sobre servicios en temporada alta."))

    # 9. Flujos intrarregionales
    if "es_intrarregional" in df.columns and tot > 0:
        w = df.loc[df["es_intrarregional"] == 1, "total_anual"].sum() / tot * 100
        r = (df["es_intrarregional"] == 1).mean() * 100
        out.append(_ind("% de viajes intrarregionales",
                        "Suma de total_anual con es_intrarregional = 1 / suma total x 100",
                        f"{pct(w)} de los viajes ({pct(r)} de los registros)",
                        "Parte del turismo que ocurre dentro de la misma región de origen: "
                        "indica el peso del turismo de cercanía."))

    # 10. Región con más viajes
    if len(estac) and tot > 0:
        t = estac.iloc[0]
        out.append(_ind("Región destino con más viajes",
                        "Suma de total_anual por región destino; se elige el máximo",
                        f"{t['region']} ({fmt(t['viajes_totales'], 0)} viajes, "
                        f"{pct(t['viajes_totales'] / tot * 100)} del total)",
                        "Principal receptor de turismo del período; ayuda a priorizar dónde "
                        "analizar la estacionalidad con más detalle."))

    # 11. Valor máximo y registro asociado
    f = df.loc[df["total_anual"].idxmax()]
    out.append(_ind("Valor máximo de total_anual y registro asociado",
                    "Fila con el mayor total_anual",
                    f"{fmt(f['total_anual'], 0)} {UNIDAD}: {f.get('comuna_origen', '?')} a "
                    f"{f.get('comuna_destino', '?')} ({int(f['anio'])})",
                    "Ruta de mayor flujo individual; es el valor extremo del gráfico 04."))

    # 12. Casos críticos
    if dist:
        out.append(_ind("Casos críticos (rutas de flujo extremo)",
                        "Registros con total_anual mayor al percentil 99 de los registros con flujo "
                        f"(= {fmt(dist['p99'], 0)})",
                        f"{fmt(dist['n_criticos'], 0)} registros, que concentran "
                        f"{pct(dist['pct_viajes_criticos'])} de todos los viajes",
                        "Un pequeño grupo de rutas explica gran parte del flujo total; son las "
                        "más relevantes para la gestión turística."))
    return pd.DataFrame(out)
