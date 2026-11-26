"""Genera tablero.html con las gráficas y la analítica de todas las pruebas; se abre con doble clic.

Uso: python tablero.py [otros.xlsx ...] [--sin-abrir]
Lee datos/lote3/ y los Excel adicionales indicados en la línea de comandos.
"""
import json
import math
import sys
import webbrowser
from datetime import date
from pathlib import Path

import numpy as np

from analizar_prueba import comparar, estadistica
from analisis_vigente import MIN_RENDIMIENTO
from fisica import RAIZ, caidas, energia, filtrar, leer_pruebas, limpiar, orden, potencia, todas_las_pruebas

MAX_PUNTOS = 1500   # por serie: suficiente para la gráfica y mantiene el HTML liviano
SALIDA = RAIZ / "tablero.html"


def lista(x, dec=4):
    return [None if v is None or not math.isfinite(v) else round(float(v), dec) for v in np.asarray(x, float)]


def limpio(o):
    """NaN e infinitos a null: JSON no los admite."""
    if isinstance(o, dict):
        return {k: limpio(v) for k, v in o.items()}
    if isinstance(o, list):
        return [limpio(v) for v in o]
    if isinstance(o, (float, np.floating)):
        return float(o) if math.isfinite(o) else None
    if isinstance(o, np.integer):
        return int(o)
    return o


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
        "n": n, "nombre": nombre or "sin nombre", "fuente": fuente, "archivo": archivo,
        "duracion": float(d.h.max()), "lecturas": len(d), "validas": len(ok),
        "e_ent": e_ent, "e_sal": e_sal, "v_sal": float(ok.Vs.mean()), "sigma_vs": float(1000 * np.std(ok.Vs)),
        "p_ent": float(ok.P.mean()), "p_sal": float(ok.Ps.mean()),
        "eficiencia": float(100 * ok.Ps.mean() / ok.P.mean()) if fuente == "bateria" and len(ok) >= MIN_RENDIMIENTO else None,
        "spark": lista(filtrar(ok.V, ok.t)[:: max(1, len(ok) // 48)], 3),  # miniatura para la tarjeta
        "comp": comp.to_dict("records"),
        "est": [{"Magnitud": k, **v} for k, v in est.to_dict("index").items()],
        "caidas": cai.round(3).head(200).to_dict("records"), "n_caidas": len(cai),
        # Hueco en horas a partir del cual la línea se corta en vez de unir puntos lejanos.
        "hueco": max(60, 3 * paso * dt) / 3600, "series": series,
    }


def main():
    extra = [Path(a) for a in sys.argv[1:] if not a.startswith("--")]
    pruebas = []
    fuentes = [todas_las_pruebas()] + [((f"P{n}", nom, fu, f.name, d) for n, nom, fu, d in leer_pruebas(f)) for f in extra]
    for gen in fuentes:
        try:
            for pid, nombre, fuente, archivo, d in gen:
                p = ficha(pid, nombre, fuente, archivo, d)
                if p:
                    pruebas.append(p)
                else:
                    print(f"  {archivo} {pid}: muy pocas filas válidas, se omite")
        except Exception as e:  # un archivo malo no detiene los demás
            print(f"  no se pudo leer ({e})")
    if not pruebas:
        sys.exit("No hay pruebas para mostrar.")
    pruebas.sort(key=lambda p: orden(p["n"]) if p["n"][1:].isdigit() else ("Z", 0))
    datos = json.dumps(limpio({"generado": date.today().isoformat(), "pruebas": pruebas}),
                       ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    plantilla = (RAIZ / "tablero_plantilla.html").read_text(encoding="utf-8")
    # "<" escapado: un nombre con "</script>" no puede romper la página.
    SALIDA.write_text(plantilla.replace("__DATOS__", datos.replace("<", r"\u003c")), encoding="utf-8")
    print(f"{len(pruebas)} pruebas -> {SALIDA.name} ({SALIDA.stat().st_size / 1e6:.1f} MB)")
    if "--sin-abrir" not in sys.argv:
        webbrowser.open(SALIDA.as_uri())


if __name__ == "__main__":
    for flujo in (sys.stdout, sys.stderr):
        flujo.reconfigure(errors="replace")  # la consola de Windows no tiene Ω ni η
    main()
