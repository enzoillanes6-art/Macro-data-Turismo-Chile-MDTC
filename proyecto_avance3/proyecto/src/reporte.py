"""Bitácora de ejecución y generación del resumen en Markdown para el informe."""
import pandas as pd


def nuevo_registro():
    """Estructura donde cada módulo anota lo que hizo (para justificarlo en el informe)."""
    return {
        "mapeo_columnas": {},
        "eliminaciones": [],     # {motivo, filas}
        "correcciones": [],      # {accion, afectados}
        "nulos": [],             # {variable, estrategia, justificacion}
        "transformaciones": [],  # {original, transformacion, resultado, tipo_final}
    }


def registrar(registro, categoria, **datos):
    registro[categoria].append(datos)


def _tabla(encabezados, filas):
    lineas = ["| " + " | ".join(encabezados) + " |",
              "| " + " | ".join(["---"] * len(encabezados)) + " |"]
    for f in filas:
        lineas.append("| " + " | ".join(str(x) for x in f) + " |")
    return "\n".join(lineas)


def construir_resumen(antes, despues, registro, df_final, validaciones):
    inverso = {nuevo: viejo for viejo, nuevo in registro["mapeo_columnas"].items()}
    cols_originales_norm = set(registro["mapeo_columnas"].values())
    nuevas = [c for c in df_final.columns if c not in cols_originales_norm]
    transformadas = {t["original"] for t in registro["transformaciones"]} - set(nuevas)

    comparacion = _tabla(
        ["Indicador", "Antes", "Después"],
        [
            ["Filas", f"{antes['filas']:,}", f"{despues['filas']:,}"],
            ["Columnas", antes["columnas"], despues["columnas"]],
            ["Valores nulos", f"{antes['nulos_total']:,}", f"{despues['nulos_total']:,}"],
            ["Filas duplicadas", f"{antes['duplicados']:,}", f"{despues['duplicados']:,}"],
            ["Identificadores repetidos (origen-destino-año)",
             f"{antes['ids_repetidos']:,}", f"{despues['ids_repetidos']:,}"],
            ["Valores fuera de rango", f"{antes['fuera_rango_total']:,}",
             f"{despues['fuera_rango_total']:,}"],
            ["Variables transformadas", 0, len(transformadas)],
            ["Variables nuevas", 0, len(nuevas)],
        ],
    )

    diag_cols = _tabla(
        ["Columna", "Tipo", "Nulos", "% nulos"],
        [[c, antes["dtypes"][c], f"{antes['nulos'][c]:,}", f"{antes['pct_nulos'][c]:.3f}%"]
         for c in antes["nulos"].index],
    )

    filas_nulos = []
    for n in registro["nulos"]:
        v = n["variable"]
        ini = int(antes["nulos"].get(inverso.get(v, v), 0))
        fin = int(despues["nulos"].get(v, 0))
        if ini == 0:
            continue   # solo variables que tenían nulos en el original
        filas_nulos.append([v, f"{ini:,}", n["estrategia"], n["justificacion"], f"{fin:,}"])
    tabla_nulos = _tabla(["Variable", "Nulos iniciales", "Estrategia", "Justificación",
                          "Nulos finales"], filas_nulos)

    tabla_transf = _tabla(
        ["Variable original", "Transformación", "Resultado", "Tipo final"],
        [[t["original"], t["transformacion"], t["resultado"], t["tipo_final"]]
         for t in registro["transformaciones"]],
    )
    elim = _tabla(["Motivo de eliminación", "Filas eliminadas"],
                  [[e["motivo"], f"{e['filas']:,}"] for e in registro["eliminaciones"]]
                  or [["(ninguna)", 0]])
    corr = _tabla(["Corrección aplicada", "Valores afectados"],
                  [[c["accion"], f"{c['afectados']:,}"] for c in registro["correcciones"]]
                  or [["(ninguna)", 0]])
    vals = _tabla(["Validación", "Resultado", "Detalle"],
                  [[n, "OK" if ok else "FALLA", d] for n, ok, d in validaciones])

    return "\n\n".join([
        "# Resumen de ejecución del pipeline (insumo para reportes/avance_2.pdf)",
        "## 1. Diagnóstico inicial (dataset original)", diag_cols,
        "Fuera de rango por columna: " + (", ".join(
            f"{k}: {v:,}" for k, v in antes["fuera_rango"].items() if v) or "ninguno"),
        "## 2. Correcciones", corr,
        "## 3. Registros eliminados", elim,
        "## 4. Tratamiento de nulos", tabla_nulos,
        "## 5. Transformaciones", tabla_transf,
        "## 6. Validaciones finales", vals,
        "## 7. Comparación antes / después", comparacion,
    ]) + "\n"


def guardar_resumen(texto, ruta):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(texto, encoding="utf-8")
