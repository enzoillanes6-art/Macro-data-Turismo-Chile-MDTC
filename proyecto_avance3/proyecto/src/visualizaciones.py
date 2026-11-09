"""Gráficos con Pyplot (Avance 3, actividad C). Guarda PNG en resultados/graficos/."""
import matplotlib

matplotlib.use("Agg")  # sin ventana: funciona desde main.py y en servidores
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import FuncFormatter

from src.configuracion import DIR_GRAFICOS, MESES_CORTOS, UNIDAD, fmt
from src.validaciones import MESES

AZUL, ROJO, NARANJA, GRIS = "#1f6f9f", "#c8372d", "#e08a1e", "#555555"
PALETA = ["#1f6f9f", "#e08a1e", "#2e9e6b", "#8e5ea2", "#c8372d"]
_miles = FuncFormatter(lambda x, _: fmt(x, 0))


def _guardar(fig, nombre):
    DIR_GRAFICOS.mkdir(parents=True, exist_ok=True)
    ruta = DIR_GRAFICOS / nombre
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta


def grafico_01_evolucion(anuales):
    """Líneas: total nacional de viajes por año (tendencia)."""
    fig, ax = plt.subplots(figsize=(9, 5.2))
    x, y = [int(a) for a in anuales.index], anuales.to_numpy() / 1e6
    ax.plot(x, y, marker="o", lw=2.2, color=AZUL, label=f"Total nacional de {UNIDAD}")
    for xi, yi in zip(x, y):
        abajo = len(y) > 2 and yi == y.min()   # la etiqueta del mínimo va debajo para no cruzar la línea
        ax.annotate(fmt(yi, 1), (xi, yi), textcoords="offset points",
                    xytext=(0, -15 if abajo else 8), ha="center", fontsize=8.5)
    ax.set_title("Evolución anual del flujo turístico nacional")
    ax.set_xlabel("Año")
    ax.set_ylabel(f"{UNIDAD.capitalize()} (millones)")
    ax.set_xticks(x)
    ax.set_ylim(0, max(y) * 1.18 if len(y) else 1)
    ax.grid(alpha=0.3)
    ax.legend(loc="lower right")
    return _guardar(fig, "grafico_01.png")


def grafico_02_estacionalidad(estac, mensual_nac):
    """Líneas: % del flujo anual por mes en las 5 regiones destino con más viajes."""
    fig, ax = plt.subplots(figsize=(9, 5.4))
    x = np.arange(12)
    for i, (_, r) in enumerate(estac.head(5).iterrows()):
        ax.plot(x, [r[f"pct_{m}"] for m in MESES], marker="o", ms=4, lw=1.8,
                color=PALETA[i], label=r["region"])
    if mensual_nac.sum() > 0:
        ax.plot(x, (mensual_nac / mensual_nac.sum() * 100).to_numpy(), ls="--", lw=2.4,
                color="black", label="Total nacional")
    ax.axhline(100 / 12, color=GRIS, lw=0.9, ls=":", label="Reparto uniforme (8,3%)")
    ax.set_title("Estacionalidad mensual por región destino")
    ax.set_xlabel("Mes")
    ax.set_ylabel("% del flujo anual de la región")
    ax.set_xticks(x)
    ax.set_ylim(bottom=0)
    ax.set_xticklabels(MESES_CORTOS)
    ax.grid(alpha=0.3)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.13), ncol=4, fontsize=8.5, frameon=False)
    return _guardar(fig, "grafico_02.png")


def grafico_03_verano_regiones(estac):
    """Barras: % del flujo anual concentrado en dic-feb por región destino."""
    d = estac.sort_values("pct_verano")
    fig, ax = plt.subplots(figsize=(9, 6))
    barras = ax.barh(d["region"], d["pct_verano"], color=AZUL, label="% del flujo en dic-feb")
    ax.axvline(25, color=ROJO, ls="--", lw=1.6, label="Reparto uniforme (25%)")
    for b, v in zip(barras, d["pct_verano"]):
        ax.text(v + 0.3, b.get_y() + b.get_height() / 2, fmt(v, 1) + "%", va="center", fontsize=8.5)
    ax.set_title("Concentración del flujo en verano (dic-feb) por región destino")
    ax.set_xlabel("% del flujo anual en diciembre, enero y febrero")
    ax.set_ylabel("Región destino")
    ax.set_xlim(0, max(d["pct_verano"].max() * 1.12, 30))
    ax.grid(axis="x", alpha=0.3)
    ax.legend(loc="lower right")
    return _guardar(fig, "grafico_03.png")


def grafico_04_distribucion(df):
    """Histograma (escala log10) del total anual por registro con flujo."""
    s = df.loc[df["total_anual"] > 0, "total_anual"]
    fig, ax = plt.subplots(figsize=(9, 5.2))
    logs = np.log10(s.to_numpy())
    ax.hist(logs, bins=60, color=AZUL, edgecolor="white", label="Registros con flujo")
    ax.axvline(np.log10(s.median()), color=NARANJA, lw=2, label=f"Mediana ({fmt(s.median(), 0)})")
    ax.axvline(np.log10(s.mean()), color=ROJO, lw=2, ls="--", label=f"Media ({fmt(s.mean(), 0)})")
    bajo, top = int(np.ceil(logs.min())), int(np.floor(logs.max()))
    marcas = list(range(bajo, top + 1)) or [int(round(logs.mean()))]
    ax.set_xlim(logs.min() - 0.15, logs.max() + 0.15)
    ax.set_xticks(marcas)
    ax.set_xticklabels([fmt(10.0 ** k, 0 if k >= 0 else 2) for k in marcas])
    ax.yaxis.set_major_formatter(_miles)
    ax.set_title("Distribución del total anual por registro origen-destino")
    ax.set_xlabel(f"{UNIDAD.capitalize()} por registro y año (escala logarítmica)")
    ax.set_ylabel("Cantidad de registros")
    ax.grid(axis="y", alpha=0.3)
    ax.legend()
    return _guardar(fig, "grafico_04.png")


def generar_graficos(df, anuales, estac, mensual_nac):
    """Genera los 4 gráficos y devuelve sus rutas (el 01-03 son los exigidos; el 04 es adicional)."""
    rutas = [grafico_01_evolucion(anuales)]
    if len(estac):
        rutas += [grafico_02_estacionalidad(estac, mensual_nac), grafico_03_verano_regiones(estac)]
    rutas.append(grafico_04_distribucion(df))
    return rutas
