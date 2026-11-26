"""Ficha de cualquier prueba del ESP32: gráficas, estadística y teórico contra real.

Uso: python analizar_prueba.py [archivo.xlsx ...] [--r OHM] [--fuente paneles|bateria|carga]
Sin archivo abre un selector. Resultado en la carpeta fichas/.
"""
import argparse
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from fisica import RAIZ, caidas, eficiencia, con_huecos, energia, error_pct, filtrar, leer_pruebas, limpiar, ohm_i, potencia

V_CONSIGNA = 5.0    # salida ajustada del MT3608
SALIDA = RAIZ / "fichas"


def comparar(d, ok, fuente, r_nom):
    """Tabla teórico contra real; d trae todas las filas y ok solo las válidas."""
    filas = []

    def fila(magnitud, teo, real, unidad, metodo):
        filas.append({"Magnitud": magnitud, "Teórico": round(teo, 3), "Real": round(real, 3), "Unidad": unidad,
                      "Error (%)": round(float(error_pct(teo, real)), 2), "Cómo se obtiene": metodo})

    for lado, v, i, p in (("entrada", "V", "I", "P_esp"), ("salida", "Vs", "Is", "Ps_esp")):
        fila(f"Potencia {lado}", potencia(ok[v], ok[i]).mean(), ok[p].mean(), "mW", "P = V·I contra la que guardó el ESP32")
    e_ent, e_sal = energia(d.t, potencia(d.V, d.I))[-1], energia(d.t, potencia(d.Vs, d.Is))[-1]
    fila("Energía entrada", e_ent, d.E_esp.dropna().iloc[-1], "mWh", "trapecios (Python) contra rectángulos (ESP32)")
    fila("Energía salida", e_sal, d.Es_esp.dropna().iloc[-1], "mWh", "trapecios (Python) contra rectángulos (ESP32)")
    fila("Tensión salida", V_CONSIGNA, ok.Vs.median(), "V", "consigna del MT3608 contra la medida")
    if r_nom:
        fila("Corriente salida", ohm_i(ok.Vs, r_nom).mean(), ok.Is.mean(), "mA", f"Ohm I = V/R con R = {r_nom:g} Ω")
        fila("Resistencia carga", r_nom, (ok.Vs / (ok.Is / 1000)).median(), "Ω", "R = V/I medida contra la nominal")
    return pd.DataFrame(filas)


def estadistica(ok):
    cols = {"V": "Tensión entrada (V)", "I": "Corriente entrada (mA)", "Vs": "Tensión salida (V)",
            "Is": "Corriente salida (mA)"}
    e = ok[list(cols)].agg(["mean", "std", "min", "max"]).T.round(3)
    e.columns = ["Media", "Desv. estándar", "Mínimo", "Máximo"]
    return e.rename(index=cols)


def graficar(d, titulo, archivo):
    fig, ejes = plt.subplots(2, 2, figsize=(13, 8), sharex=True)
    pares = [("Tensión (V)", "V", "Vs"), ("Corriente (mA)", "I", "Is"), ("Potencia (mW)", "P", "Ps")]
    d = d.assign(P=potencia(d.V, d.I), Ps=potencia(d.Vs, d.Is))
    for ax, (nombre, a, b) in zip(ejes.flat, pares):
        for col, color, etq in ((a, "#1f5fa8", "entrada"), (b, "#e08a00", "salida")):
            s = d[["t", col]].dropna()
            if s.empty:
                continue
            ax.plot(*con_huecos(s.t / 3600, s[col], hueco=60/3600), color=color, alpha=.25, lw=.8)
            ax.plot(*con_huecos(s.t / 3600, filtrar(s[col], s.t), hueco=60/3600), color=color, lw=1.8, label=etq)
        ax.set_ylabel(nombre)
        ax.grid(alpha=.3)
        ax.legend(loc="best")
    ax = ejes[1, 1]
    ax.plot(d.h, energia(d.t, d.P), color="#1f5fa8", label="entrada")
    ax.plot(d.h, energia(d.t, d.Ps), color="#e08a00", label="salida")
    ax.set_ylabel("Energía acumulada (mWh)")
    ax.grid(alpha=.3)
    ax.legend(loc="best")
    for ax in ejes[1]:
        ax.set_xlabel("Tiempo (h)")
    fig.suptitle(titulo + "  ·  línea clara: medida  ·  línea fuerte: filtrada", fontsize=12)
    fig.tight_layout()
    fig.savefig(archivo, dpi=130)
    plt.close(fig)


def ficha(destino, comp, est, cai, ok):
    """Excel con las cuatro tablas; destino puede ser una ruta o un BytesIO."""
    with pd.ExcelWriter(destino) as x:
        comp.to_excel(x, sheet_name="Teórico vs real", index=False)
        est.to_excel(x, sheet_name="Estadística")
        cai.to_excel(x, sheet_name="Caídas de tensión", index=False)
        ok.drop(columns="fecha").to_excel(x, sheet_name="Datos limpios", index=False)


def analizar(archivo, r_nom=None, forzar=None):
    indice = []
    for n, nombre, fuente, d in leer_pruebas(archivo):
        fuente = forzar or fuente
        ok = limpiar(d)
        clave = f"{Path(archivo).stem}_P{n}"
        if len(ok) < 10:
            print(f"  Prueba {n}: solo {len(ok)} filas válidas, se omite")
            continue
        carpeta = SALIDA / clave
        carpeta.mkdir(parents=True, exist_ok=True)
        titulo = f"Prueba {n} · {nombre or 'sin nombre'} · fuente: {fuente}"
        comp, est = comparar(d, ok, fuente, r_nom), estadistica(ok)
        cai = caidas(ok.t, ok.Vs, ok.Is)
        graficar(d, titulo, carpeta / "graficas.png")
        ficha(carpeta / "ficha.xlsx", comp, est, cai, ok)
        if fuente == "bateria" and len(ok) >= 100:
            print(f"  Eficiencia por potencia: {eficiencia(potencia(ok.Vs, ok.Is).mean(), potencia(ok.V, ok.I).mean()):.2f} %")
        print(f"\n{titulo}\n  {len(d)} filas, {len(d) - len(ok)} descartadas, {d.h.max():.2f} h, {len(cai)} caídas bruscas")
        print(comp.drop(columns="Cómo se obtiene").to_string(index=False))
        indice.append({"Ficha": clave, "Prueba": n, "Nombre": nombre, "Fuente": fuente,
                       "Duración (h)": round(d.h.max(), 2), "Filas válidas": len(ok),
                       "E entrada (mWh)": comp.Real[2], "E salida (mWh)": comp.Real[3]})
    return indice


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("archivos", nargs="*", help="Excel descargados de la página del ESP32")
    ap.add_argument("--r", type=float, help="resistencia nominal de la carga en Ω, para comparar con Ohm")
    ap.add_argument("--fuente", choices=["paneles", "bateria", "carga"], help="si el Excel no la trae o es otra")
    a = ap.parse_args()
    if not a.archivos:
        from tkinter import Tk, filedialog
        Tk().withdraw()
        a.archivos = filedialog.askopenfilenames(title="Excel del ESP32", filetypes=[("Excel", "*.xlsx")])
    nuevos = []
    for f in a.archivos:
        print(f"\n== {Path(f).name}")
        try:
            nuevos += analizar(f, a.r, a.fuente)
        except Exception as e:  # un archivo malo no detiene los demás
            print(f"  No se pudo leer: {e}")
    if not nuevos:
        sys.exit("Nada que analizar.")
    # Índice de todas las fichas: clasifica las pruebas analizadas hasta ahora.
    ruta = SALIDA / "indice.csv"
    viejo = pd.read_csv(ruta) if ruta.exists() else pd.DataFrame()
    nuevo = pd.DataFrame(nuevos)
    todo = pd.concat([viejo[~viejo.Ficha.isin(nuevo.Ficha)] if len(viejo) else viejo, nuevo])
    todo.sort_values(["Fuente", "Prueba"]).to_csv(ruta, index=False, encoding="utf-8-sig")
    print(f"\nListo: {len(nuevos)} ficha(s) en {SALIDA}")


if __name__ == "__main__":
    for flujo in (sys.stdout, sys.stderr):
        flujo.reconfigure(errors="replace")  # la consola de Windows no tiene Ω ni η
    main()
