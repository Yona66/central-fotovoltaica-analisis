"""Genera tablero.html con las gráficas y la analítica de todas las pruebas; se abre con doble clic.

Uso: python tablero.py [otros.xlsx ...] [--sin-abrir]
Lee todos los Excel de datos/ (para sumar una prueba nueva basta con copiarla ahí).
"""
import json
import math
import sys
import webbrowser
from pathlib import Path

import numpy as np

from analizar_prueba import comparar, estadistica
from fisica import DATOS, LOTE1, RAIZ, caidas, energia, filtrar, leer_pruebas, limpiar, potencia

MAX_PUNTOS = 1500   # por serie: suficiente para la gráfica y mantiene el HTML liviano
SALIDA = RAIZ / "tablero.html"


def lista(x, dec=4):
    return [None if v is None or not math.isfinite(v) else round(float(v), dec) for v in np.asarray(x, float)]


def ficha(n, nombre, fuente, archivo, d):
    d = d.assign(P=potencia(d.V, d.I), Ps=potencia(d.Vs, d.Is))
    d = d.assign(E=energia(d.t, d.P), Es=energia(d.t, d.Ps))
    ok = limpiar(d)
    if len(ok) < 10:
        return None
    comp, est, cai = comparar(d, ok, fuente, None), estadistica(ok), caidas(ok.t, ok.Vs, ok.Is)
    paso = max(1, math.ceil(len(ok) / MAX_PUNTOS))
    series = {"h": lista(ok.h[::paso], 5)}
    for c in ("V", "Vs", "I", "Is", "P", "Ps"):
        series[c] = lista(filtrar(ok[c], ok.t)[::paso])
        series[c + "_crudo"] = lista(ok[c].to_numpy()[::paso])
    for c in ("E", "Es"):
        series[c] = lista(ok[c].to_numpy()[::paso], 2)
    dt = np.median(np.diff(ok.t)) if len(ok) > 1 else 5
    e_ent, e_sal = float(comp.Real[2]), float(comp.Real[3])
    return {
        "n": int(n), "nombre": nombre or "sin nombre", "fuente": fuente, "archivo": archivo,
        "duracion": float(d.h.max()), "lecturas": len(d), "validas": len(ok),
        "e_ent": e_ent, "e_sal": e_sal, "v_sal": float(ok.Vs.mean()), "sigma_vs": float(1000 * np.std(ok.Vs)),
        "comp": comp.to_dict("records"),
        "est": [{"Magnitud": k, **v} for k, v in est.to_dict("index").items()],
        "caidas": cai.round(3).head(200).to_dict("records"), "n_caidas": len(cai),
        # Hueco en horas a partir del cual la línea se corta en vez de unir puntos lejanos.
        "hueco": max(60, 3 * paso * dt) / 3600, "series": series,
    }


def main():
    archivos = sorted(DATOS.rglob("*.xlsx")) + [Path(a) for a in sys.argv[1:] if not a.startswith("--")]
    pruebas = []
    for f in archivos:
        try:
            for n, nombre, fuente, d in leer_pruebas(f):
                if n in LOTE1 and f.name.startswith(f"central_pv_prueba{n}_2026-10-22"):  # recorte del notebook: luego el sensor se movió
                    fuente, t_max = LOTE1[n]
                    d = d[d.t < t_max]
                p = ficha(n, nombre, fuente, f.name, d)
                if p:
                    pruebas.append(p)
                else:
                    print(f"  {f.name} P{n}: muy pocas filas válidas, se omite")
        except Exception as e:  # un archivo malo no detiene los demás
            print(f"  {f.name}: no se pudo leer ({e})")
    if not pruebas:
        sys.exit("No hay pruebas para mostrar.")
    pruebas.sort(key=lambda p: p["n"])
    datos = json.dumps(pruebas, ensure_ascii=False, separators=(",", ":"), default=float).replace("NaN", "null")
    plantilla = (RAIZ / "tablero_plantilla.html").read_text(encoding="utf-8")
    SALIDA.write_text(plantilla.replace("__DATOS__", datos), encoding="utf-8")
    print(f"{len(pruebas)} pruebas -> {SALIDA.name} ({SALIDA.stat().st_size / 1e6:.1f} MB)")
    if "--sin-abrir" not in sys.argv:
        webbrowser.open(SALIDA.as_uri())


if __name__ == "__main__":
    for flujo in (sys.stdout, sys.stderr):
        flujo.reconfigure(errors="replace")  # la consola de Windows no tiene Ω ni η
    main()
