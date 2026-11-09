"""Genera reportes/avance_3.pdf con el formato de los informes anteriores (portada UA, logo, secciones
numeradas, bibliografía). Todas las cifras e interpretaciones se calculan con los datos reales."""
from datetime import date
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (CondPageBreak, Image, KeepTogether, PageBreak, Paragraph, Preformatted,
                                SimpleDocTemplate, Spacer, Table, TableStyle)

from src.configuracion import RUTA_RESPUESTAS, UNIDAD, URL_REPOSITORIO, VERANO, fmt, pct

# ---- datos de la portada (editar si corresponde)
TITULO_PROYECTO = "Macro-data Turismo Chile"
GRUPO = "Grupo 14"
INTEGRANTES = ["Benjamín Aguayo", "Enzo Illanes", "Jaime Panguinao"]
PROFESOR = "Alex Flores"
CURSO = "Programación Avanzada"
LOGO = Path(__file__).resolve().parent / "logo_ua.png"

ROJO_TITULO = colors.HexColor("#B01513")
ROJO = colors.HexColor("#C00000")
GRIS = colors.HexColor("#7F7F7F")
FONDO_CAB = colors.HexColor("#E4ECF3")
_E = getSampleStyleSheet()
ESTILOS = {
    "t": ParagraphStyle("t", parent=_E["Title"], fontName="Helvetica", fontSize=28, leading=32, alignment=0,
                        textColor=ROJO_TITULO, spaceAfter=8),
    "h1": ParagraphStyle("h1", parent=_E["Heading1"], fontName="Helvetica-Bold", fontSize=12.5, leading=16,
                         textColor=ROJO, spaceBefore=14, spaceAfter=5),
    "h2": ParagraphStyle("h2", parent=_E["Heading2"], fontName="Helvetica-Bold", fontSize=11.5, leading=15,
                         textColor=colors.black, spaceBefore=9, spaceAfter=4),
    "h3": ParagraphStyle("h3", parent=_E["Heading3"], fontName="Helvetica-Bold", fontSize=10.5, leading=14,
                         textColor=colors.black, spaceBefore=7, spaceAfter=3),
    "p": ParagraphStyle("p", parent=_E["BodyText"], fontName="Helvetica", fontSize=10.5, leading=15.5,
                        alignment=4, spaceAfter=6),
    "c": ParagraphStyle("c", parent=_E["BodyText"], fontName="Helvetica", fontSize=8.5, leading=11,
                        textColor=colors.HexColor("#444444"), spaceAfter=6),
    "bib": ParagraphStyle("bib", parent=_E["BodyText"], fontName="Helvetica", fontSize=10.5, leading=15.5,
                          alignment=4, leftIndent=22, bulletIndent=8, spaceAfter=4),
    "centro": ParagraphStyle("centro", parent=_E["Heading1"], fontName="Helvetica-Bold", fontSize=12, leading=16,
                             textColor=ROJO, alignment=1, spaceBefore=22, spaceAfter=10),
    "celda": ParagraphStyle("celda", parent=_E["BodyText"], fontSize=7.4, leading=9),
    "celdah": ParagraphStyle("celdah", parent=_E["BodyText"], fontSize=7.4, leading=9, fontName="Helvetica-Bold"),
    "celda_s": ParagraphStyle("celda_s", parent=_E["BodyText"], fontSize=6.6, leading=8, splitLongWords=0),
    "celdah_s": ParagraphStyle("celdah_s", parent=_E["BodyText"], fontSize=6.6, leading=8, splitLongWords=0,
                               fontName="Helvetica-Bold"),
    "portada": ParagraphStyle("portada", parent=_E["BodyText"], fontSize=10.5, leading=12.5),
    "aviso": ParagraphStyle("aviso", parent=_E["BodyText"], fontSize=10, leading=14, textColor=ROJO),
}


def _s(texto):
    """Deja el texto compatible con las fuentes estándar del PDF (cp1252) y lo escapa."""
    reemplazos = {"→": " a ", "–": "-", "—": "-", "−": "-", "≥": ">=", "≤": "<=", "·": "*", "\0": ""}
    texto = str(texto)
    for a, b in reemplazos.items():
        texto = texto.replace(a, b)
    return escape(texto.encode("cp1252", "replace").decode("cp1252"))


def P(texto, estilo="p"):
    return Paragraph(_s(texto), ESTILOS[estilo])


def PB(etiqueta, texto):
    return Paragraph(f"<b>{_s(etiqueta)}</b> {_s(texto)}", ESTILOS["p"])


def PBullet(etiqueta, texto):
    """Viñeta con etiqueta en negrita, como en los informes anteriores."""
    return Paragraph(f"<b>{_s(etiqueta)}</b> {_s(texto)}", ESTILOS["bib"], bulletText="•")


def _tabla(filas, anchos, repetir=1, chica=False):
    eh, ec = ("celdah_s", "celda_s") if chica else ("celdah", "celda")
    datos = [[Paragraph(_s(x), ESTILOS[eh]) for x in filas[0]]]
    datos += [[Paragraph(_s(x), ESTILOS[ec]) for x in f] for f in filas[1:]]
    t = Table(datos, colWidths=[a * cm for a in anchos], repeatRows=repetir)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), FONDO_CAB),
        ("LINEBELOW", (0, 0), (-1, 0), 0.6, colors.HexColor("#8aa4b8")),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, colors.HexColor("#d5dde4")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def _imagen(ruta, ancho_cm=15.5):
    w, h = ImageReader(str(ruta)).getSize()
    return Image(str(ruta), width=ancho_cm * cm, height=ancho_cm * cm * h / w)


def _g(num, var, col):
    f = num[num["variable"] == var]
    return f.iloc[0][col] if len(f) else np.nan


def _lista(items):
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " y " + items[-1]


# =============================================================== TEXTOS (calculados con los datos)
def _texto_estadisticas(c):
    num, frec, N = c["num"], c["frec"], c["n_filas"]
    out = []
    media, med = _g(num, "total_anual", "media"), _g(num, "total_anual", "mediana")
    cv, ceros = _g(num, "total_anual", "cv_pct"), _g(num, "total_anual", "pct_ceros")
    if med > 0 and media / med > 1.5:
        asim = (f"la media es {fmt(media / med, 1)} veces la mediana, lo que revela una distribución muy "
                "asimétrica hacia la derecha: la mayoría de los pares origen-destino registra pocos viajes "
                "y unos pocos concentran volúmenes enormes")
    elif med == 0:
        asim = "la mediana es 0, es decir, más de la mitad de los registros no tiene flujo en el año"
    else:
        asim = "media y mediana son similares, por lo que la distribución es relativamente simétrica"
    disp = "muy alta" if cv > 100 else ("alta" if cv > 50 else "moderada")
    out.append(
        f"La variable principal es total_anual ({UNIDAD} por registro origen-destino-año). Su media es "
        f"{fmt(media)} y su mediana {fmt(med)}: {asim}. La desviación estándar ({fmt(_g(num, 'total_anual', 'desv_estandar'))}) "
        f"equivale al {fmt(cv, 0)}% de la media (coeficiente de variación), una dispersión {disp}. El rango va de "
        f"{fmt(_g(num, 'total_anual', 'minimo'))} a {fmt(_g(num, 'total_anual', 'maximo'))} y el 50% central de los "
        f"registros (Q1 a Q3) está entre {fmt(_g(num, 'total_anual', 'q1'))} y {fmt(_g(num, 'total_anual', 'q3'))}. "
        f"Además, {pct(ceros)} de los registros no tiene flujo.")

    pv = _g(num, "pct_verano", "media")
    if not np.isnan(pv):
        out.append(
            f"La variable pct_verano (porcentaje del flujo anual de cada registro en diciembre, enero y febrero) "
            f"tiene un promedio de {pct(pv)} y una mediana de {pct(_g(num, 'pct_verano', 'mediana'))}. Como un reparto "
            f"uniforme pondría 25% del flujo en esos tres meses, el valor observado queda "
            f"{fmt(abs(pv - 25), 1)} puntos {'por sobre' if pv > 25 else 'por debajo de'} lo esperado: "
            f"{'el verano concentra más viajes que un mes promedio' if pv > 25 else 'el verano no domina de forma general'}.")

    meses = num[num["variable"].isin(["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
                                      "septiembre", "octubre", "noviembre", "diciembre"])]
    if len(meses) == 12 and meses["media"].min() > 0:
        o = meses.sort_values("media", ascending=False)
        out.append(
            f"Entre los 12 meses, los de mayor flujo medio por registro son {_lista(o['variable'].head(3))} y el de menor "
            f"flujo es {o['variable'].iloc[-1]}; el mes más alto ({o['variable'].iloc[0]}) supera "
            f"{fmt(o['media'].iloc[0] / o['media'].iloc[-1], 2)} veces al más bajo, evidencia inicial de estacionalidad.")

    partes = []
    r = frec[(frec["variable"] == "region_destino")]
    if len(r):
        partes.append(f"la región destino más frecuente es {r.iloc[0]['categoria']} ({pct(r.iloc[0]['porcentaje'])} de los registros)")
    r = frec[(frec["variable"] == "es_intrarregional") & (frec["categoria"] == "1")]
    if len(r):
        partes.append(f"{pct(r.iloc[0]['porcentaje'])} de los registros son viajes dentro de la misma región")
    r = frec[(frec["variable"] == "mes_pico")]
    if len(r):
        top = r.sort_values("frecuencia", ascending=False).iloc[0]
        partes.append(f"el mes pico más común es {top['categoria']} ({pct(top['porcentaje'])})")
    r = frec[(frec["variable"] == "anio")]
    if len(r):
        partes.append(f"cada año aporta entre {pct(r['porcentaje'].min())} y {pct(r['porcentaje'].max())} de los registros")
    if partes:
        out.append("En las variables categóricas: " + "; ".join(partes) +
                   ". La variable nivel_flujo se construyó con terciles de los registros con flujo, por lo que sus "
                   "categorías bajo, medio y alto son parejas por diseño; 'sin flujo' agrupa los registros con total 0.")
    return out


def _tendencia(anuales):
    anios, v = [int(a) for a in anuales.index], anuales.to_numpy()
    cambios = [(anios[i], (v[i] - v[i - 1]) / v[i - 1] * 100) for i in range(1, len(v)) if v[i - 1] > 0]
    return anios, v, cambios


def _texto_graficos(c):
    anuales, estac, nat, dist = c["anuales"], c["estac"], c["mensual_nac"], c["dist"]
    g = []

    # ---- gráfico 01
    anios, v, cambios = _tendencia(anuales)
    d = {"titulo": "Gráfico 01: Evolución anual del flujo turístico nacional",
         "archivo": "grafico_01.png",
         "vars": f"Año (eje X) y total nacional de {UNIDAD} (eje Y, millones), calculado como la suma de total_anual "
                 "de todos los pares origen-destino de cada año."}
    if len(v) >= 2 and v[0] > 0:
        var = (v[-1] - v[0]) / v[0] * 100
        caidas = [f"{a} ({p:+.1f}%)".replace(".", ",") for a, p in cambios if p < 0]
        d["patron"] = (f"Entre {anios[0]} y {anios[-1]} el flujo total {'creció' if var > 0 else 'disminuyó'} "
                       f"{fmt(abs(var), 1)}% (de {fmt(v[0] / 1e6, 1)} a {fmt(v[-1] / 1e6, 1)} millones). " +
                       (f"Hubo caídas respecto del año anterior en {_lista(caidas)}." if caidas
                        else "La serie no presenta caídas interanuales."))
        imax, imin = int(np.argmax(v)), int(np.argmin(v))
        ext = (f"El año de mayor flujo fue {anios[imax]} ({fmt(v[imax] / 1e6, 1)} millones) y el de menor flujo "
               f"{anios[imin]} ({fmt(v[imin] / 1e6, 1)} millones).")
        if cambios:
            a_min, p_min = min(cambios, key=lambda x: x[1])
            if p_min < 0:
                ext += f" La mayor caída interanual ocurrió en {a_min} ({fmt(p_min, 1)}%)" + \
                       (", coincidente con el efecto de la pandemia de COVID-19 sobre la movilidad." if a_min in (2020, 2021) else ".")
        d["extremos"] = ext
    else:
        d["patron"] = "El dataset usado contiene un solo año, por lo que no es posible describir una tendencia."
        d["extremos"] = "No aplica."
    d["ayuda"] = ("Responde directamente la primera parte de la pregunta del proyecto (qué tendencia presenta el "
                  "flujo en los últimos años) y permite identificar períodos anómalos que conviene tratar con cuidado "
                  "al proyectar el flujo futuro.")
    g.append(d)

    # ---- gráfico 02
    if len(estac):
        pico_n, min_n = nat.idxmax(), nat.idxmin()
        top5 = estac.head(5)
        modo = top5["mes_pico"].value_counts()
        hi, lo = top5.loc[top5["pct_verano"].idxmax()], top5.loc[top5["pct_verano"].idxmin()]
        fuera = [f"{r['region']} (pico en {r['mes_pico']})" for _, r in estac.iterrows() if r["mes_pico"] not in VERANO]
        rango = estac["pct_verano"].max() - estac["pct_verano"].min()
        d = {"titulo": "Gráfico 02: Estacionalidad mensual por región destino",
             "archivo": "grafico_02.png",
             "vars": "Mes (eje X) y porcentaje del flujo anual de cada región destino que ocurre en ese mes (eje Y). "
                     "Se muestran las 5 regiones con más viajes, el total nacional (línea punteada negra) y el reparto "
                     "uniforme de 8,3% por mes."}
        d["patron"] = (f"A nivel nacional el flujo se concentra en {pico_n} ({pct(nat[pico_n] / nat.sum() * 100)} del total anual) "
                       f"y es mínimo en {min_n} ({pct(nat[min_n] / nat.sum() * 100)}). De las {len(top5)} regiones graficadas, "
                       f"{modo.iloc[0]} tienen su mes pico en {modo.index[0]}.")
        d["extremos"] = (f"{hi['region']} es la más veraniega ({pct(hi['pct_verano'])} de su flujo en dic-feb) y "
                         f"{lo['region']} la de reparto más parejo ({pct(lo['pct_verano'])}). " +
                         (f"Con pico fuera del verano: {_lista(fuera)}." if fuera else
                          "Todas las regiones tienen su mes pico en verano."))
        d["ayuda"] = ("Responde la segunda parte de la pregunta: la estacionalidad " +
                      ("varía de forma relevante entre regiones" if rango > 5 else "es bastante similar entre regiones") +
                      f" (la concentración estival difiere {fmt(rango, 1)} puntos entre la región más y menos veraniega), "
                      "y muestra en qué meses se debería reforzar la oferta turística de cada una.")
        g.append(d)

        # ---- gráfico 03
        sobre = int((estac["pct_verano"] > 25).sum())
        top3 = estac.sort_values("pct_verano", ascending=False).head(3)["region"].tolist()
        a, b = estac.loc[estac["pct_verano"].idxmax()], estac.loc[estac["pct_verano"].idxmin()]
        d = {"titulo": "Gráfico 03: Concentración del flujo en verano por región destino",
             "archivo": "grafico_03.png",
             "vars": "Región destino (eje Y) y porcentaje de su flujo anual ocurrido en diciembre, enero y febrero "
                     "(eje X). La línea roja marca 25%, lo esperado si el flujo se repartiera parejo."}
        d["patron"] = (f"{sobre} de las {len(estac)} regiones superan el 25% de su flujo en verano; el promedio regional es "
                       f"{pct(estac['pct_verano'].mean())}. Las más veraniegas son {_lista(top3)}.")
        d["extremos"] = (f"La brecha entre {a['region']} ({pct(a['pct_verano'])}) y {b['region']} ({pct(b['pct_verano'])}) "
                         f"es de {fmt(a['pct_verano'] - b['pct_verano'], 1)} puntos porcentuales." +
                         (f" Regiones con pico fuera del verano: {_lista(fuera)}." if fuera else ""))
        d["ayuda"] = ("Ordena a las regiones por su dependencia del verano en una sola cifra comparable, lo que permite "
                      "clasificarlas (muy estacionales vs. de demanda más pareja) y priorizar medidas de gestión de temporada.")
        g.append(d)

    # ---- gráfico 04
    if dist:
        d = {"titulo": "Gráfico 04: Distribución del total anual por registro",
             "archivo": "grafico_04.png",
             "vars": f"Cantidad de {UNIDAD} por registro origen-destino-año (eje X, escala logarítmica) frente a la "
                     "cantidad de registros (eje Y), considerando solo registros con flujo mayor a 0."}
        d["patron"] = (f"La distribución es muy asimétrica: la mediana ({fmt(dist['mediana'])}) queda por debajo de la media "
                       f"({fmt(dist['media'])}); {pct(dist['pct_menor_100'])} de los registros con flujo tiene menos de 100 viajes "
                       f"y {pct(dist['pct_menor_1000'])} menos de 1.000.")
        d["extremos"] = (f"El valor máximo es {fmt(dist['maximo'])}. {fmt(dist['n_criticos'], 0)} registros superan el "
                         f"percentil 99 ({fmt(dist['p99'])}) y concentran {pct(dist['pct_viajes_criticos'])} de todos los viajes.")
        d["ayuda"] = ("Justifica usar la mediana además de la media y trabajar con totales agregados (por año y por región) "
                      "para responder la pregunta, porque los registros individuales están dominados por pocas rutas extremas.")
        g.append(d)
    return g


def _ind(c, nombre):
    f = c["ind"][c["ind"]["indicador"].str.startswith(nombre)]
    return f.iloc[0] if len(f) else None


def _texto_relacion(c):
    anuales, estac, nat = c["anuales"], c["estac"], c["mensual_nac"]
    anios, v, cambios = _tendencia(anuales)
    t = []
    if len(v) >= 2 and v[0] > 0:
        var = (v[-1] - v[0]) / v[0] * 100
        t.append(f"Tendencia: el flujo nacional {'creció' if var > 0 else 'disminuyó'} {fmt(abs(var), 1)}% entre "
                 f"{anios[0]} y {anios[-1]}" +
                 (f", con caídas en {_lista([str(a) for a, p in cambios if p < 0])}." if any(p < 0 for _, p in cambios) else "."))
    if len(estac) and nat.sum() > 0:
        est = nat[VERANO].sum() / nat.sum() * 100
        hi, lo = estac.loc[estac["pct_verano"].idxmax()], estac.loc[estac["pct_verano"].idxmin()]
        t.append(f"Estacionalidad: a nivel nacional {pct(est)} del flujo ocurre entre diciembre y febrero, pero entre regiones "
                 f"la concentración estival va de {pct(lo['pct_verano'])} ({lo['region']}) a {pct(hi['pct_verano'])} "
                 f"({hi['region']}), es decir, la estacionalidad varía de forma {'importante' if hi['pct_verano'] - lo['pct_verano'] > 5 else 'moderada'} entre regiones.")
    return ("La pregunta del proyecto es: ¿qué tendencia presenta el flujo de turismo en los últimos años y cómo varía la "
            "estacionalidad entre las distintas regiones de Chile? Los resultados de este avance la responden así. " +
            " ".join(t) + " Las estadísticas descriptivas aportan el contexto (distribución asimétrica y muchos pares sin flujo) "
            "que obliga a analizar totales agregados en lugar de registros individuales.")


def _texto_preguntas(c):
    num, estac, anuales, ver = c["num"], c["estac"], c["anuales"], c["verif"]
    media, med = _g(num, "total_anual", "media"), _g(num, "total_anual", "mediana")
    cv, ceros, pv = _g(num, "total_anual", "cv_pct"), _g(num, "total_anual", "pct_ceros"), _g(num, "pct_verano", "media")
    razon = f"{fmt(media / med, 1)} veces" if med > 0 else "un valor mucho mayor que"
    q = []
    q.append(("¿Qué medida estadística resultó más útil?",
              f"La comparación entre media y mediana junto con el coeficiente de variación. Mostró que total_anual es muy asimétrica "
              f"(la media es {razon} la mediana y el CV es {fmt(cv, 0)}%), por lo que el promedio simple engaña y conviene "
              f"trabajar con totales agregados. Para estacionalidad, el promedio de pct_verano ({pct(pv)}) fue la medida más directa."))
    i1 = _ind(c, "Variación del flujo total")
    i2 = _ind(c, "Región destino más estacional")
    i3 = _ind(c, "Concentración estival")
    txt = "Para la tendencia, la variación del flujo total entre el primer y el último año"
    txt += f": {i1['resultado']}" if i1 is not None else ""
    txt += "; para la estacionalidad regional, el índice de estacionalidad y la concentración estival"
    if len(estac):
        txt += f" (pct_verano entre {pct(estac['pct_verano'].min())} y {pct(estac['pct_verano'].max())} según la región)"
    txt += ", porque resumen en una cifra comparable lo que la pregunta pide."
    q.append(("¿Qué indicador ayuda mejor a responder el problema?", txt))
    q.append(("¿Qué gráfico comunica mejor los resultados?",
              "El gráfico 02 (estacionalidad mensual por región), porque muestra en una sola figura la forma del año de cada región, "
              "el total nacional y el reparto uniforme de referencia. Para la tendencia, el gráfico 01 es el más claro."))
    ok = sum(1 for _, o, _ in ver if o)
    q.append(("¿Cómo verificaron los cálculos?",
              f"El programa ejecuta {len(ver)} comprobaciones automáticas en cada corrida ({ok} aprobadas en esta ejecución): "
              "contrasta media y mediana con NumPy, verifica que la suma por año, por región y por mes sea igual al total general, "
              "que los 12 meses sumen total_anual en cada fila, que pct_verano esté entre 0 y 100 y que los porcentajes mensuales "
              "de cada región sumen 100. El detalle está en la sección 5."))
    inesp = []
    if ceros >= 10:
        inesp.append(f"el {pct(ceros)} de registros sin flujo")
    if med > 0 and media / med > 3:
        inesp.append(f"una media {fmt(media / med, 1)} veces mayor que la mediana")
    _, _, cambios = _tendencia(anuales)
    if cambios and min(p for _, p in cambios) < -10:
        a, p = min(cambios, key=lambda x: x[1])
        inesp.append(f"la caída de {fmt(abs(p), 1)}% del flujo total en {a}")
    if len(estac):
        fuera = [r["region"] for _, r in estac.iterrows() if r["mes_pico"] not in VERANO]
        if fuera:
            inesp.append(f"el pico fuera del verano en {_lista(fuera)}")
    q.append(("¿Qué resultado fue inesperado?",
              ("Lo más inesperado fue " + _lista(inesp) + ".") if inesp else
              "No hubo resultados contradictorios; los patrones coinciden con lo esperado para el turismo interno."))
    q.append(("¿Qué análisis deberían realizar después?",
              "Un análisis de series de tiempo mensuales por región (medias móviles y descomposición estacional) para proyectar el "
              "flujo, como plantea el objetivo del proyecto; comparar regiones de origen y destino; medir el efecto de eventos "
              "puntuales (por ejemplo la pandemia) sobre la tendencia; estudiar las rutas críticas a nivel comunal y contrastar "
              "con pruebas de hipótesis si las diferencias de estacionalidad entre regiones son estadísticamente significativas."))
    return q


def _texto_conclusion(c):
    n_ind, n_graf = len(c["ind"]), len(c["graficos"])
    return (f"En este avance se calcularon estadísticas descriptivas para {c['num'].shape[0]} variables numéricas y las frecuencias de "
            f"{c['frec']['variable'].nunique()} variables categóricas, se programaron {n_ind} indicadores y se generaron {n_graf} gráficos, "
            "todo exportado automáticamente con python main.py a la carpeta resultados/. " + _texto_relacion(c).split("Los resultados de este avance la responden así. ")[1] +
            " Como limitaciones, el análisis agrega registros de una matriz origen-destino muy dispersa y asimétrica, por lo que las "
            "conclusiones se basan en totales y porcentajes agregados; el siguiente avance puede profundizar con modelos de series de "
            "tiempo y proyección del flujo.")


MARCA_BORRADOR = "<!-- BORRADOR"
TITULO_CONCLUSION = "Conclusión del avance"


def _cargar_respuestas(c):
    """Devuelve (preguntas, conclusión). Lee reportes/respuestas_finales.md; si no existe lo crea
    como borrador con los textos automáticos, para que el equipo los reescriba con sus palabras."""
    auto, concl = _texto_preguntas(c), _texto_conclusion(c)
    if not RUTA_RESPUESTAS.exists():
        lineas = [MARCA_BORRADOR + ": reescriban las respuestas con lo que realmente vivieron y BORREN esta línea. "
                  "Cada título '## ' es una pregunta del informe; el texto debajo es su respuesta. "
                  "Vuelvan a ejecutar python main.py para actualizar el PDF. -->", ""]
        for q, a in auto:
            lineas += [f"## {q}", a, ""]
        lineas += [f"## {TITULO_CONCLUSION}", concl, ""]
        RUTA_RESPUESTAS.parent.mkdir(parents=True, exist_ok=True)
        RUTA_RESPUESTAS.write_text("\n".join(lineas), encoding="utf-8")
        return auto, concl
    secciones, actual = [], None
    for linea in RUTA_RESPUESTAS.read_text(encoding="utf-8").splitlines():
        if linea.startswith("<!--"):
            continue
        if linea.startswith("## "):
            actual = [linea[3:].strip(), []]
            secciones.append(actual)
        elif actual is not None and linea.strip():
            actual[1].append(linea.strip())
    textos = [(q, " ".join(cuerpo)) for q, cuerpo in secciones if cuerpo]
    preguntas = [(q, a) for q, a in textos if q != TITULO_CONCLUSION]
    conclusion = next((a for q, a in textos if q == TITULO_CONCLUSION), concl)
    return (preguntas or auto), conclusion



def _log_recortado(log, max_lineas=85):
    lineas = [l[:125] for l in log.rstrip().splitlines()]
    if len(lineas) > max_lineas:
        lineas = lineas[:25] + ["[... salida intermedia omitida; el texto completo está en reportes/ejecucion_avance3.txt ...]"] + lineas[-(max_lineas - 26):]
    return _s("\n".join(lineas)).replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")




# =============================================================== CONSTRUCCIÓN DEL PDF
ARBOL = """proyecto/
|-- main.py                  # Orquestador: ejecuta el Avance 2 y el Avance 3
|-- requirements.txt         # Dependencias (pandas, numpy, matplotlib, reportlab)
|-- verificar_entrega.py     # Revisa la lista final de entrega
|-- src/
|   |-- carga.py             # Lectura e ingesta de datos            (Avance 2)
|   |-- limpieza.py          # Filtrado y saneamiento                (Avance 2)
|   |-- transformaciones.py  # Variables derivadas y casting         (Avance 2)
|   |-- validaciones.py      # Validaciones de esquema e integridad  (Avance 2)
|   |-- reporte.py           # Bitacora y resumen del Avance 2       (Avance 2)
|   |-- estadisticas.py      # Estadistica descriptiva               (Avance 3)
|   |-- indicadores.py       # Indicadores automatizados             (Avance 3)
|   |-- visualizaciones.py   # Graficos con Pyplot                   (Avance 3)
|   |-- informe.py           # Genera reportes/avance_3.pdf          (Avance 3)
|   `-- configuracion.py     # Rutas, constantes y carga del dataset (Avance 3)
|-- datos/
|   |-- originales/          # Data cruda (input)
|   `-- procesados/          # dataset_limpio.csv (output del Avance 2)
|-- resultados/              # estadisticas.csv, indicadores.csv, graficos/
`-- reportes/                # avance_3.pdf"""


def _logo(canvas):
    if LOGO.exists():
        w = 102
        h = w * 138 / 320
        canvas.drawImage(ImageReader(str(LOGO)), 566 - w, LETTER[1] - 35 - h, width=w, height=h, mask="auto")


def _pagina(canvas, doc):
    canvas.saveState()
    _logo(canvas)
    canvas.restoreState()


def _portada(canvas, doc):
    canvas.saveState()
    _logo(canvas)
    canvas.setFillColor(GRIS)
    canvas.setFont("Helvetica-Bold", 15)
    canvas.drawCentredString(LETTER[0] / 2, 674, "PROGRAMACIÓN AVANZADA")
    canvas.drawCentredString(LETTER[0] / 2, 658.5, "ING. CIVIL PLAN COMUN\u2013 SEDE TEMUCO")
    canvas.setFillColor(ROJO_TITULO)
    canvas.setFont("Helvetica-Bold", 20)
    canvas.drawCentredString(LETTER[0] / 2, 477, "\u201c" + TITULO_PROYECTO + "\u201d")
    canvas.restoreState()


def _tabla_portada():
    filas = [("Nº Grupo", GRUPO), ("Integrantes", INTEGRANTES[0])]
    filas += [("", n) for n in INTEGRANTES[1:]]
    filas += [("Profesor", PROFESOR), ("Curso", CURSO), ("", ""),
              ("Fecha", date.today().strftime("%d/%m/%Y")), ("Nota", "")]
    nb = "\u00a0"   # espacio duro: mantiene la altura de las filas vacías
    datos = [[Paragraph(_s(a or nb), ESTILOS["portada"]), Paragraph(":" if a else nb, ESTILOS["portada"]),
              Paragraph(_s(b or nb), ESTILOS["portada"])] for a, b in filas]
    t = Table(datos, colWidths=[92, 16, 175], hAlign="RIGHT")
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                           ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    return t


def construir_informe(c, ruta_pdf):
    """c: diccionario con n_filas, ruta_datos, num, frec, ind, estac, anuales, mensual_nac, dist, verif, log, graficos."""
    ruta_pdf.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(ruta_pdf), pagesize=LETTER, leftMargin=2.5 * cm, rightMargin=2.5 * cm,
                            topMargin=3.0 * cm, bottomMargin=2.2 * cm,
                            title="Informe Nº3: Estadística e indicadores", author=f"{GRUPO} - {CURSO}")
    s = []
    # ---------------- portada
    s += [Spacer(1, 353), _tabla_portada(), PageBreak()]

    # ---------------- resumen
    n_ind, n_graf = len(c["ind"]), len(c["graficos"])
    a0, a1 = c["anios"]
    s.append(P("INFORME Nº3", "t"))
    if "muestra" in str(c["ruta_datos"]):
        s.append(P("ADVERTENCIA: este informe se generó con la muestra del dataset (dataset_limpio_muestra.csv), no con el "
                   "dataset completo. Los resultados son solo referenciales: vuelva a ejecutar con dataset_limpio.csv.", "aviso"))
    s.append(Paragraph(
        "<b>Resumen del Avance:</b> " + _s(
            f"En este tercer avance se programó la estadística descriptiva del dataset limpio, se automatizaron {n_ind} indicadores "
            f"relacionados con la pregunta del proyecto y se exportaron tablas (CSV), {n_graf} gráficos (PNG) y este informe de forma "
            f"automática mediante main.py, a partir de {fmt(c['n_filas'], 0)} registros de la matriz de movilidad turística comunal "
            f"origen-destino ({a0}-{a1})."), ESTILOS["p"]))

    # ---------------- 1
    s.append(P("1. Descripción del Trabajo Desarrollado", "h1"))
    s.append(P("En la Sesión 3 de desarrollo se extendió la estructura modular del Avance 2 incorporando la etapa de análisis sobre "
               "el dataset limpio (datos/procesados/dataset_limpio.csv). Se programaron tres módulos nuevos (estadisticas.py, "
               "indicadores.py y visualizaciones.py) y main.py ejecuta todo el proceso con un único comando, generando "
               "automáticamente las tablas, los gráficos y este informe. El trabajo busca responder la pregunta del proyecto: "
               "¿qué tendencia presenta el flujo de turismo en los últimos años y cómo varía la estacionalidad entre las distintas "
               "regiones de Chile?"))

    # ---------------- 2
    s.append(P("2. Componentes e Implementación Técnica", "h1"))
    s.append(P("2.1. Modularización de la Aplicación", "h2"))
    s.append(P("El código se organizó en módulos independientes con responsabilidades únicas dentro de la arquitectura del software:"))
    s.append(Preformatted(ARBOL, ParagraphStyle("arbol", fontName="Courier", fontSize=6.9, leading=8.6,
                                                backColor=colors.HexColor("#F3F5F7"), borderPadding=5, spaceAfter=10)))

    s.append(P("2.2. Estadística Descriptiva", "h2"))
    s.append(P("El módulo estadisticas.py calcula, para cada variable numérica, la cantidad de registros, media, mediana, mínimo, "
               "máximo, rango, desviación estándar y cuartiles, y las frecuencias de las variables categóricas. Los resultados se "
               "exportan a resultados/estadisticas.csv."))
    s.append(P("Variables numéricas", "h3"))
    cab = ["Variable", "n", "Media", "Mediana", "Mín.", "Máx.", "Rango", "Desv. est.", "Q1", "Q3", "CV %", "% ceros"]
    filas = [cab]
    for _, r in c["num"].iterrows():
        filas.append([r["variable"], fmt(r["n_registros"], 0), fmt(r["media"]), fmt(r["mediana"]), fmt(r["minimo"]),
                      fmt(r["maximo"]), fmt(r["rango"]), fmt(r["desv_estandar"]), fmt(r["q1"]), fmt(r["q3"]),
                      fmt(r["cv_pct"], 0), fmt(r["pct_ceros"], 1)])
    s.append(_tabla(filas, [2.3, 1.55, 1.4, 1.3, 0.95, 1.55, 1.55, 1.35, 1.1, 1.25, 1.0, 1.05], chica=True))
    s.append(P("Cada mes está expresado en " + UNIDAD + " por registro; total_anual es la suma de los 12 meses; pct_verano es el "
               "porcentaje del flujo anual en dic-feb; CV = desviación estándar / media.", "c"))
    s.append(P("Variables categóricas (frecuencias)", "h3"))
    top = {"anio": 10, "es_intrarregional": 2, "nivel_flujo": 4, "mes_pico": 6, "region_destino": 6, "region_origen": 6}
    filas = [["Variable", "Categoría", "Frecuencia", "% de registros"]]
    for var, k in top.items():
        sub = c["frec"][c["frec"]["variable"] == var]
        if var == "mes_pico":
            sub = sub.sort_values("frecuencia", ascending=False)
        for _, r in sub.head(k).iterrows():
            filas.append([var, r["categoria"], fmt(r["frecuencia"], 0), fmt(r["porcentaje"], 1) + "%"])
    s.append(_tabla(filas, [3.6, 6.0, 3.2, 3.2]))
    s.append(P("Se muestran las categorías más frecuentes; el detalle completo está en resultados/estadisticas.csv.", "c"))
    s.append(P("Interpretación", "h3"))
    for t in _texto_estadisticas(c):
        s.append(P(t))

    s.append(P("2.3. Indicadores Automatizados", "h2"))
    s.append(P(f"El módulo indicadores.py calcula {n_ind} indicadores (el mínimo exigido es 5) directamente relacionados con la "
               "pregunta del proyecto; se recalculan en cada ejecución y se exportan a resultados/indicadores.csv. La tabla de "
               "estacionalidad por región se exporta a resultados/estacionalidad_regional.csv."))
    filas = [["Indicador", "Método de cálculo", "Resultado", "Interpretación"]]
    for _, r in c["ind"].iterrows():
        filas.append([r["indicador"], r["metodo_calculo"], r["resultado"], r["interpretacion"]])
    s.append(_tabla(filas, [3.3, 4.2, 3.6, 5.1]))

    s.append(P("2.4. Gráficos con Pyplot", "h2"))
    s.append(P("El módulo visualizaciones.py genera los gráficos y los guarda como PNG en resultados/graficos/. Cada gráfico incluye "
               "título, nombre de los ejes, unidad de medida y leyenda."))
    rutas = {p.name: p for p in c["graficos"]}
    for d in _texto_graficos(c):
        if d["archivo"] not in rutas:
            continue
        s.append(KeepTogether([P(d["titulo"], "h3"), _imagen(rutas[d["archivo"]], 13.5)]))
        s.append(PBullet("¿Qué variables representa?", d["vars"]))
        s.append(PBullet("¿Qué patrón se observa?", d["patron"]))
        s.append(PBullet("¿Existen diferencias o valores extremos?", d["extremos"]))
        s.append(PBullet("¿Cómo ayuda a responder la pregunta del proyecto?", d["ayuda"]))
        s.append(Spacer(1, 6))

    s.append(P("2.5. Verificación de los Cálculos", "h2"))
    s.append(P("En cada ejecución el programa contrasta sus resultados con cálculos independientes:"))
    s.append(_tabla([["Comprobación", "Resultado", "Detalle"]] +
                    [[n, "OK" if ok else "FALLA", d] for n, ok, d in c["verif"]], [8.0, 2.0, 6.2]))

    s.append(P("2.6. Evidencia de Ejecución de main.py", "h2"))
    s.append(P("Salida de consola al ejecutar python main.py desde la raíz del proyecto (versión completa en "
               "reportes/ejecucion_avance3.txt):"))
    s.append(Preformatted(_log_recortado(c["log"]), ParagraphStyle(
        "log", fontName="Courier", fontSize=5.9, leading=7.0, backColor=colors.HexColor("#F3F5F7"), borderPadding=4)))

    # ---------------- 3-6
    s.append(P("3. Relación de los Resultados con la Pregunta del Proyecto", "h1"))
    s.append(P(_texto_relacion(c)))
    s.append(P("4. Preguntas Finales", "h1"))
    preguntas, conclusion = _cargar_respuestas(c)
    for preg, resp in preguntas:
        s.append(PBullet(preg, resp))
    s.append(P("5. Conclusiones", "h1"))
    s.append(P(conclusion))
    s.append(P("6. Enlace al Repositorio", "h1"))
    s.append(Paragraph(f"<link href='{URL_REPOSITORIO}' color='blue'>{URL_REPOSITORIO}</link>", ESTILOS["p"]))

    s.append(P("Bibliografía", "centro"))
    for ref in (
            "McKinney, W. (2022). Python for Data Analysis: Data Wrangling with Pandas, NumPy, and Jupyter (3rd ed.). O'Reilly Media.",
            "Sweigart, A. (2019). Automate the Boring Stuff with Python: Practical Programming for Total Beginners (2nd ed.). No Starch Press.",
            "Hunter, J. D. (2007). Matplotlib: A 2D graphics environment. Computing in Science & Engineering, 9(3), 90-95.",
            "Harris, C. R., et al. (2020). Array programming with NumPy. Nature, 585, 357-362."):
        s.append(Paragraph(_s(ref), ESTILOS["bib"], bulletText="•"))

    final = []   # los títulos no quedan solos al final de una página
    for f in s:
        if isinstance(f, Paragraph) and f.style.name in ("h1", "h2"):
            final.append(CondPageBreak(4.5 * cm))
        final.append(f)
    doc.build(final, onFirstPage=_portada, onLaterPages=_pagina)
    return ruta_pdf
