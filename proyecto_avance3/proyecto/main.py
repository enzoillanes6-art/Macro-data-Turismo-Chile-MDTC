"""Ejecuta TODO el proyecto desde la raíz:  python main.py

Avance 2: carga -> diagnóstico -> limpieza -> nulos -> transformaciones -> validación -> exportación.
Avance 3: estadísticas -> indicadores -> gráficos -> informe PDF (usa dataset_limpio.csv).

Opciones:
  --solo-avance3   omite el pipeline del Avance 2 y usa el dataset_limpio.csv ya generado.
"""
import io
import sys
from pathlib import Path

import pandas as pd

from src import carga, limpieza, transformaciones as tr, validaciones as val, reporte
from src.configuracion import (RUTA_ESTACIONALIDAD, RUTA_ESTADISTICAS, RUTA_INDICADORES,
                               RUTA_INFORME, RUTA_LOG, DIR_RESULTADOS, cargar_limpio)
from src.estadisticas import calcular_estadisticas, verificar_calculos
from src.indicadores import (calcular_indicadores, resumen_distribucion, tabla_estacionalidad,
                             totales_anuales, totales_mensuales_nacional)
from src.visualizaciones import generar_graficos

RAIZ = Path(__file__).resolve().parent
SALIDA = RAIZ / "datos" / "procesados" / "dataset_limpio.csv"
RESUMEN = RAIZ / "reportes" / "resumen_ejecucion.md"


class _Tee:
    """Copia lo que se imprime en pantalla a un buffer (evidencia de ejecución para el informe)."""

    def __init__(self, *flujos):
        self.flujos = flujos

    def write(self, texto):
        for f in self.flujos:
            f.write(texto)

    def flush(self):
        for f in self.flujos:
            f.flush()


def ejecutar_avance2():
    """Avance 2: limpieza y transformación. Devuelve 0 (ok), 1 (error) o 2 (validaciones con fallas)."""
    registro = reporte.nuevo_registro()

    print("1. CARGA")
    ruta = carga.localizar_original(RAIZ)
    if ruta is None:
        print("No se encontró el dataset. Colócalo en datos/originales/dataset.csv "
              "(ver datos/instrucciones_descarga.txt).")
        return 1
    df = carga.cargar_datos(ruta)
    if df is None:
        return 1
    print(f"Archivo: {ruta.relative_to(RAIZ)} (solo lectura)")

    print("\n2. DIAGNÓSTICO INICIAL")
    antes = val.diagnosticar(df)
    val.imprimir_diagnostico(antes, "Dataset original")

    print("\n3. LIMPIEZA")
    df = limpieza.normalizar_nombres_columnas(df, registro)
    df = limpieza.limpiar_espacios(df, registro)
    df = limpieza.unificar_categorias(df, registro)
    df = limpieza.corregir_fuera_de_rango(df, registro)
    df = limpieza.eliminar_duplicados(df, registro)
    limpieza.revisar_ids_repetidos(df, registro)

    print("4. TRATAMIENTO DE NULOS")
    df = limpieza.tratar_nulos(df, registro)

    print("5. TRANSFORMACIONES")
    df = tr.convertir_tipos(df, registro)
    df = tr.crear_fecha(df, registro)
    df = tr.crear_total_anual(df, registro)
    df = tr.crear_mes_pico(df, registro)
    df = tr.crear_porcentaje_verano(df, registro)
    df = tr.crear_intrarregional(df, registro)
    df = tr.clasificar_nivel_flujo(df, registro)

    print("6. VALIDACIÓN")
    resultados = val.validar(df)
    for nombre, ok, detalle in resultados:
        print(f"  [{'OK' if ok else 'FALLA'}] {nombre}: {detalle}")
    despues = val.diagnosticar(df)
    val.imprimir_diagnostico(despues, "Dataset procesado")

    print("\n7. EXPORTACIÓN")
    ruta_csv, ruta_muestra = carga.guardar_datos(df, SALIDA)
    reporte.guardar_resumen(
        reporte.construir_resumen(antes, despues, registro, df, resultados), RESUMEN)
    print(f"  {ruta_csv.relative_to(RAIZ)}  ({ruta_csv.stat().st_size / 1e6:.1f} MB)")
    print(f"  {ruta_muestra.relative_to(RAIZ)}")
    print(f"  {RESUMEN.relative_to(RAIZ)}  (tablas listas para el informe)")
    return 0 if all(ok for _, ok, _ in resultados) else 2



def ejecutar_avance3():
    """Avance 3: estadísticas, indicadores, gráficos e informe. Devuelve el contexto del informe."""
    print("\n" + "=" * 70 + "\nAVANCE 3: ESTADÍSTICA E INDICADORES\n" + "=" * 70)
    print("8. CARGA DEL DATASET LIMPIO")
    df, ruta = cargar_limpio()
    print(f"  {ruta.relative_to(RAIZ)}: {len(df):,} filas x {df.shape[1]} columnas")
    DIR_RESULTADOS.mkdir(exist_ok=True)

    print("\n9. ESTADÍSTICAS DESCRIPTIVAS")
    tabla, num, frec = calcular_estadisticas(df)
    tabla.to_csv(RUTA_ESTADISTICAS, index=False, encoding="utf-8-sig")
    print(f"  -> {RUTA_ESTADISTICAS.relative_to(RAIZ)} ({len(tabla)} filas)")
    with pd.option_context("display.float_format", "{:,.2f}".format, "display.width", 150,
                           "display.max_columns", 12):
        print(num[["variable", "n_registros", "media", "mediana", "minimo", "maximo", "desv_estandar"]]
              .to_string(index=False))

    print("\n10. INDICADORES")
    anuales, nat = totales_anuales(df), totales_mensuales_nacional(df)
    estac, dist = tabla_estacionalidad(df), resumen_distribucion(df)
    ind = calcular_indicadores(df, anuales, estac, dist)
    ind.to_csv(RUTA_INDICADORES, index=False, encoding="utf-8-sig")
    estac.to_csv(RUTA_ESTACIONALIDAD, index=False, encoding="utf-8-sig")
    print(f"  -> {RUTA_INDICADORES.relative_to(RAIZ)} ({len(ind)} indicadores)")
    print(f"  -> {RUTA_ESTACIONALIDAD.relative_to(RAIZ)} ({len(estac)} regiones)")
    for _, r in ind.iterrows():
        print(f"  - {r['indicador']}: {r['resultado']}")

    print("\n11. VERIFICACIÓN DE CÁLCULOS")
    verif = verificar_calculos(df, num, anuales, estac)
    for nombre, ok, detalle in verif:
        print(f"  [{'OK' if ok else 'FALLA'}] {nombre}: {detalle}")

    print("\n12. GRÁFICOS")
    graficos = generar_graficos(df, anuales, estac, nat)
    for g in graficos:
        print(f"  -> {g.relative_to(RAIZ)}")

    return {"n_filas": len(df), "ruta_datos": ruta, "num": num, "frec": frec, "ind": ind,
            "estac": estac, "anuales": anuales, "mensual_nac": nat, "dist": dist, "verif": verif,
            "graficos": graficos, "anios": (int(df["anio"].min()), int(df["anio"].max()))}


def main():
    for flujo in (sys.stdout, sys.stderr):      # evita errores de tildes en consolas de Windows
        if hasattr(flujo, "reconfigure"):
            flujo.reconfigure(encoding="utf-8", errors="replace")
    buffer = io.StringIO()
    sys.stdout = _Tee(sys.__stdout__, buffer)
    try:
        codigo = 0
        if "--solo-avance3" in sys.argv:
            print("Se omite el pipeline del Avance 2 (--solo-avance3).")
        elif carga.localizar_original(RAIZ) is not None:
            codigo = ejecutar_avance2()
            if codigo == 1:
                return 1
        else:
            print("No se encontró datos/originales/dataset.csv: se omite el pipeline del Avance 2 "
                  "y se usa el dataset limpio existente.")

        try:
            contexto = ejecutar_avance3()
        except (FileNotFoundError, ValueError) as e:
            print(f"\nERROR: {e}")
            return 1

        print("\n13. INFORME PDF")
        contexto["log"] = buffer.getvalue()
        RUTA_LOG.parent.mkdir(parents=True, exist_ok=True)
        try:
            from src.informe import construir_informe
            construir_informe(contexto, RUTA_INFORME)
            print(f"  -> {RUTA_INFORME.relative_to(RAIZ)}")
        except ImportError:
            print("  AVISO: falta la librería reportlab; instálala con 'pip install -r requirements.txt' "
                  "para generar reportes/avance_3.pdf. Las tablas y gráficos sí se generaron.")
        RUTA_LOG.write_text(buffer.getvalue(), encoding="utf-8")
        if codigo == 2:
            print("\nNota: el Avance 2 terminó con validaciones en FALLA (ver sección 6); el Avance 3 se ejecutó igualmente.")
        print("\nProceso completo.")
        return 0
    finally:
        sys.stdout = sys.__stdout__


if __name__ == "__main__":
    raise SystemExit(main())
