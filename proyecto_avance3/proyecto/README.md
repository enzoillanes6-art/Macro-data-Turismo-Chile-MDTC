# Proyecto 14: Evolución del Turismo Nacional e Internacional

- **Institución:** Universidad Autónoma de Chile · **Asignatura:** Programación Avanzada
- **Docente:** Alex Flores Fuentealba
- **Integrantes:** Benjamín Aguayo, Enzo Illanes, Jaime Panguinao
- **Repositorio:** https://github.com/BenjaAgx/Macro-data-Turismo-Chile-MDTC-
- **Avance actual:** Avance 3 – Estadística e indicadores

## Descripción
Análisis de la matriz de movilidad turística comunal (SERNATUR / INE) para identificar tendencias
y estacionalidad del flujo de visitantes. Este avance deja el dataset listo para el análisis
mediante un pipeline reproducible en Python + Pandas.

## Pipeline
```
datos/originales/dataset.csv  (solo lectura)
   ↓ carga.py            Lectura (sep ';', latin-1, decimal ',')
   ↓ validaciones.py     Diagnóstico inicial (nulos, duplicados, fuera de rango)
   ↓ limpieza.py         Nombres de columnas, espacios, categorías, rangos, duplicados
   ↓ limpieza.py         Tratamiento de nulos (estrategia por variable)
   ↓ transformaciones.py Tipos, fecha, total_anual, mes_pico, pct_verano, es_intrarregional, nivel_flujo
   ↓ validaciones.py     Validación de columnas, tipos y rangos
   ↓ carga.py            datos/procesados/dataset_limpio.csv
   ↓ estadisticas.py     resultados/estadisticas.csv
   ↓ indicadores.py      resultados/indicadores.csv (+ estacionalidad_regional.csv)
   ↓ visualizaciones.py  resultados/graficos/grafico_01..04.png
   ↓ informe.py          reportes/avance_3.pdf
```

## Estructura
```
├── datos/
│   ├── originales/            # dataset.csv original (no se versiona ni se modifica)
│   ├── procesados/            # dataset_limpio.csv (+ muestra de 1000 filas)
│   ├── README.md
│   └── instrucciones_descarga.txt
├── resultados/                # estadisticas.csv, indicadores.csv, estacionalidad_regional.csv, graficos/ (autogenerado)
├── reportes/                  # avance_1.pdf, avance_2.pdf, avance_3.pdf (autogenerado), resumen_ejecucion.md
├── src/
│   ├── __init__.py
│   ├── carga.py               # lectura y escritura de archivos
│   ├── limpieza.py            # normalización, duplicados, rangos y nulos
│   ├── transformaciones.py    # conversión de tipos y variables nuevas
│   ├── validaciones.py        # diagnóstico y validación de columnas, tipos y rangos
│   ├── reporte.py             # bitácora de cambios y resumen en Markdown
│   ├── configuracion.py       # (Avance 3) rutas, constantes y carga del dataset limpio
│   ├── estadisticas.py        # (Avance 3) estadística descriptiva y verificación de cálculos
│   ├── indicadores.py         # (Avance 3) indicadores y tabla de estacionalidad regional
│   ├── visualizaciones.py     # (Avance 3) gráficos con Pyplot
│   └── informe.py             # (Avance 3) genera reportes/avance_3.pdf
├── main.py
└── requirements.txt
```

## Requisitos
Python 3.13 (el código no usa nada específico de una versión; las versiones mínimas de `requirements.txt` son las primeras con soporte para 3.13).

## Instrucciones de ejecución
1. Clonar: `git clone https://github.com/BenjaAgx/Macro-data-Turismo-Chile-MDTC-.git && cd Macro-data-Turismo-Chile-MDTC-`
2. Descargar `dataset.csv` (164 MB) desde el enlace de `datos/instrucciones_descarga.txt` y guardarlo en `datos/originales/dataset.csv`.
3. Instalar dependencias: `pip install -r requirements.txt`
4. Ejecutar desde la raíz: `python main.py`

Salidas: `datos/procesados/dataset_limpio.csv` y `reportes/resumen_ejecucion.md`
(tablas de diagnóstico, nulos, transformaciones y comparación antes/después para el informe).

## Decisiones de limpieza (resumen)
| Tema | Decisión |
| --- | --- |
| Duplicados exactos | Se elimina la repetición y se conserva la primera |
| Identificadores repetidos (origen-destino-año) | Se informan, no se modifican |
| Flujos negativos / códigos de región fuera de 1-16 | Pasan a nulo y se tratan como nulos |
| Año fuera de 2018-2025 o nulo | Se elimina la fila |
| Códigos y nombres territoriales nulos | Se recuperan desde su par código↔nombre; si no, `desconocido` o se elimina |
| Meses nulos | Fila sin ningún mes: se elimina. Resto: 0 + columna `n_meses_imputados` |
| Otras columnas con nulos | Mediana (numéricas) o `desconocido` (texto) |

Toda eliminación y corrección queda registrada en `reportes/resumen_ejecucion.md`.

## Avance 3: estadística, indicadores y gráficos
`python main.py` ejecuta **todo** desde la raíz: el pipeline del Avance 2 (si existe `datos/originales/dataset.csv`)
y luego el Avance 3 sobre `datos/procesados/dataset_limpio.csv`. Si el archivo completo no está, usa la muestra
`dataset_limpio_muestra.csv` (con aviso). Opción: `python main.py --solo-avance3` omite el Avance 2.

| Salida | Contenido |
| --- | --- |
| `resultados/estadisticas.csv` | n, media, mediana, mín, máx, rango, desv. estándar, cuartiles, CV, % ceros y frecuencias |
| `resultados/indicadores.csv` | 12 indicadores: método de cálculo, resultado e interpretación |
| `resultados/estacionalidad_regional.csv` | % mensual, % de verano e índice de estacionalidad por región destino |
| `resultados/graficos/grafico_01..04.png` | evolución anual, estacionalidad por región, % de verano por región, distribución |
| `reportes/avance_3.pdf` | informe con tablas, gráficos, interpretaciones, verificación y evidencia de ejecución |
| `reportes/ejecucion_avance3.txt` | salida completa de consola de la última ejecución |

| Módulo | Responsabilidad |
| --- | --- |
| `src/estadisticas.py` | Estadísticas descriptivas y verificación cruzada de cálculos |
| `src/indicadores.py` | Indicadores del proyecto (tendencia y estacionalidad) |
| `src/visualizaciones.py` | Crear y guardar los gráficos |
| `main.py` | Ejecutar todo el proceso |

### Respuestas finales y verificación de entrega
- La primera vez que se ejecuta `python main.py` se crea `reportes/respuestas_finales.md` con un **borrador** de las preguntas
  finales y la conclusión. El equipo lo reescribe con sus propias palabras, borra la línea `<!-- BORRADOR ... -->` y vuelve a
  ejecutar `python main.py` (o `python main.py --solo-avance3`) para regenerar `reportes/avance_3.pdf`.
- `python verificar_entrega.py` revisa la lista final de entrega del enunciado (archivos, módulos, README, commits, informe
  generado con el dataset completo y respuestas ya escritas).
