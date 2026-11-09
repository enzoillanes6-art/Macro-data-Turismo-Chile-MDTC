"""Revisa la lista final de entrega del Avance 3.   Uso:  python verificar_entrega.py

Estados: OK = cumplido | FALTA = hay que corregirlo | REVISAR = depende del equipo.
"""
import subprocess
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
res = []


def agregar(nombre, estado, detalle=""):
    res.append((nombre, estado, detalle))


def filas_csv(ruta):
    with open(ruta, encoding="utf-8-sig") as f:
        return max(sum(1 for _ in f) - 1, 0)


def git(*args):
    try:
        r = subprocess.run(["git", *args], cwd=RAIZ, capture_output=True, text=True, timeout=20)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


pdf = RAIZ / "reportes" / "avance_3.pdf"
agregar("Informe guardado como reportes/avance_3.pdf",
        "OK" if pdf.exists() and pdf.stat().st_size > 0 else "FALTA", "ejecuta python main.py" if not pdf.exists() else "")

for nombre, minimo in (("estadisticas.csv", 10), ("indicadores.csv", 5)):
    ruta = RAIZ / "resultados" / nombre
    if not ruta.exists():
        agregar(f"resultados/{nombre} existe", "FALTA", "ejecuta python main.py")
    else:
        n = filas_csv(ruta)
        agregar(f"resultados/{nombre} con contenido", "OK" if n >= minimo else "FALTA", f"{n} filas (mínimo {minimo})")

faltan = [f"grafico_0{i}.png" for i in (1, 2, 3) if not (RAIZ / "resultados" / "graficos" / f"grafico_0{i}.png").exists()]
agregar("Tres gráficos PNG (grafico_01 a grafico_03)", "FALTA" if faltan else "OK", ", ".join(faltan))

modulos = ["src/estadisticas.py", "src/indicadores.py", "src/visualizaciones.py", "main.py"]
sin = [m for m in modulos if not (RAIZ / m).exists()]
agregar("Código dividido en módulos + main.py", "FALTA" if sin else "OK", ", ".join(sin))

req = (RAIZ / "requirements.txt").read_text(encoding="utf-8").lower() if (RAIZ / "requirements.txt").exists() else ""
sin = [l for l in ("pandas", "numpy", "matplotlib") if l not in req]
agregar("requirements.txt con pandas, numpy y matplotlib", "FALTA" if sin else "OK", ", ".join(sin))

readme = (RAIZ / "README.md").read_text(encoding="utf-8") if (RAIZ / "README.md").exists() else ""
agregar("README.md actualizado (menciona el Avance 3)", "OK" if "Avance 3" in readme else "FALTA")

log = RAIZ / "reportes" / "ejecucion_avance3.txt"
if log.exists() and "se usa la muestra" in log.read_text(encoding="utf-8"):
    agregar("Informe generado con el dataset completo", "REVISAR",
            "se usó la muestra; ejecuta con datos/procesados/dataset_limpio.csv completo")
else:
    agregar("Informe generado con el dataset completo", "OK" if log.exists() else "REVISAR",
            "" if log.exists() else "aún no hay registro de ejecución")

resp = RAIZ / "reportes" / "respuestas_finales.md"
if not resp.exists():
    agregar("Respuestas finales y conclusión escritas por el equipo", "REVISAR", "ejecuta python main.py para crear el borrador")
elif "<!-- BORRADOR" in resp.read_text(encoding="utf-8"):
    agregar("Respuestas finales y conclusión escritas por el equipo", "REVISAR",
            "reportes/respuestas_finales.md sigue como borrador: reescríbelo, borra la línea BORRADOR y vuelve a ejecutar")
else:
    agregar("Respuestas finales y conclusión escritas por el equipo", "OK")

n = git("rev-list", "--count", "HEAD")
if n is None:
    agregar("Repositorio con commits significativos", "REVISAR", "no se detectó un repositorio git en esta carpeta")
else:
    sucio = git("status", "--porcelain")
    agregar("Repositorio con commits significativos", "OK" if int(n) >= 6 else "REVISAR", f"{n} commits (recomendado: al menos 6)")
    agregar("Todos los cambios están en commits", "OK" if not sucio else "REVISAR",
            "" if not sucio else f"{len(sucio.splitlines())} archivos con cambios sin commit")

for nombre, estado, detalle in res:
    print(f"[{estado:7}] {nombre}" + (f"  ->  {detalle}" if detalle else ""))
ok = sum(1 for _, e, _ in res if e == "OK")
print(f"\n{ok} de {len(res)} comprobaciones en OK.")
raise SystemExit(1 if any(e == "FALTA" for _, e, _ in res) else 0)
