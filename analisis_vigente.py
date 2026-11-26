"""Análisis reproducible de las ocho pruebas del montaje de noviembre."""
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from fisica import RAIZ, caidas, con_huecos, eficiencia, energia, error_pct, filtrar, limpiar, ohm_r, potencia, todas_las_pruebas

MIN_RENDIMIENTO = 100
HUECO_S = 60


def preparar():
    return {pid: (nombre, fuente, archivo, d.assign(P=potencia(d.V, d.I), Ps=potencia(d.Vs, d.Is)))
            for pid, nombre, fuente, archivo, d in todas_las_pruebas()}


def resumen(pruebas):
    filas = []
    for pid, (nombre, fuente, archivo, d) in pruebas.items():
        ok = limpiar(d)
        tramo = ok.t.diff().between(0, HUECO_S, inclusive="right")
        tiempo = ok.t.diff().where(tramo).sum() / 3600
        p_ent, p_sal = ok.P.mean(), ok.Ps.mean()
        rendimiento = fuente == "bateria" and len(ok) >= MIN_RENDIMIENTO
        e_py, es_py = (energia(d.t, d[c])[-1] for c in ("P", "Ps"))
        e_esp = d.E_esp.dropna().iloc[-1]
        filas.append({
            "prueba": pid, "nombre": nombre, "fuente": fuente, "archivo": archivo,
            "inicio": d.fecha.min().isoformat(timespec="minutes"), "duracion_h": d.h.max(),
            "horas_validas_h": tiempo, "lecturas": len(d), "validas": len(ok),
            "v_ent_V": ok.V.mean(), "i_ent_mA": ok.I.mean(), "p_ent_mW": p_ent,
            "v_sal_V": ok.Vs.mean(), "i_sal_mA": ok.Is.mean(), "p_sal_mW": p_sal,
            "energia_ent_mWh": e_py, "energia_sal_mWh": es_py, "energia_esp_mWh": e_esp,
            "error_energia_pct": error_pct(e_esp, e_py).item() if abs(e_esp) > 1 else None,
            "error_potencia_pct": np.nanmean(error_pct(ok.P_esp, ok.P)),
            "r_carga_ohm": np.nanmedian(ohm_r(ok.Vs, ok.Is)),
            "sigma_sal_mV": 1000 * np.std(ok.Vs), "error_salida_pct": error_pct(5, ok.Vs).mean(),
            "i_max_cruda_mA": d.I.max(), "saltos": len(caidas(ok.t, ok.V, ok.I)),
            "eficiencia_pct": float(eficiencia(p_sal, p_ent)) if rendimiento else None,
            "perdida_mW": p_ent - p_sal if rendimiento else None,
        })
    return pd.DataFrame(filas).set_index("prueba")


def modelos(pruebas, tabla):
    bateria = tabla.dropna(subset=["eficiencia_pct"])
    curvas, autonomias = {}, []
    for pid in bateria.index:
        d = limpiar(pruebas[pid][3])
        grupos = (d.t.diff().gt(HUECO_S) | d.t.diff().le(0)).cumsum()
        bloques = [g for _, g in d.groupby(grupos) if len(g) >= MIN_RENDIMIENTO]
        g = max(bloques, key=lambda tramo: tramo.t.iloc[-1] - tramo.t.iloc[0]).copy()
        g["h_tramo"] = (g.t - g.t.iloc[0]) / 3600
        g["V_modelo"] = np.polyval(np.polyfit(g.h_tramo, g.V, 4), g.h_tramo)
        g["eta"] = eficiencia(g.Ps, g.P)
        curvas[pid] = g
        completa = g.V.iloc[-1] < 3 and g.V.iloc[0] > 3.3
        if completa:
            autonomias.append({"prueba": pid, "medida_h": g.h_tramo.iloc[-1],
                               "energia_Wh": energia(g.t, g.P)[-1] / 1000, "potencia_mW": g.P.mean()})
    auto = pd.DataFrame(autonomias).set_index("prueba")
    auto["calculada_h"] = 1000 * (auto.energia_Wh.sum() - auto.energia_Wh) / (len(auto) - 1) / auto.potencia_mW
    auto["error_pct"] = error_pct(auto.calculada_h, auto.medida_h)
    return curvas, auto


def graficar(pruebas, tabla, curvas, auto, carpeta):
    carpeta.mkdir(exist_ok=True)

    def guardar(fig, nombre):
        fig.tight_layout()
        fig.savefig(carpeta / f"{nombre}.png", dpi=115)
        plt.close(fig)

    fig, ejes = plt.subplots(2, 1, figsize=(9, 5.4), sharex=True)
    for pid, fila in tabla[tabla.fuente.eq("paneles")].iterrows():
        d = pruebas[pid][3]
        for ax, col, unidad in zip(ejes, ("V", "I"), ("Tensión (V)", "Corriente (mA)")):
            ax.plot(*con_huecos(d.t, d[col]), lw=0.9, label=pid)
            ax.set_ylabel(unidad)
    ejes[0].legend(ncol=4)
    ejes[1].set_xlabel("Tiempo desde el inicio (s)")
    guardar(fig, "paneles")

    pid = max(pruebas, key=lambda p: len(pruebas[p][3]) - tabla.loc[p, "validas"])
    d = pruebas[pid][3]
    ok = limpiar(d)
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(*con_huecos(d.t, d.Vs), color="#9caab7", label="Cruda")
    ax.plot(*con_huecos(ok.t, filtrar(ok.Vs, ok.t)), color="#004883", label="Filtrada")
    ax.set(xlabel="Tiempo (s)", ylabel="Salida (V)", title=f"{pid} · ejemplo de limpieza")
    ax.legend()
    guardar(fig, "r1_limpieza")

    fig, ejes = plt.subplots(1, 2, figsize=(10, 4))
    for pid, g in curvas.items():
        ejes[0].plot(g.h_tramo, g.V, alpha=0.45)
        ejes[0].plot(g.h_tramo, g.V_modelo, "--", label=pid)
    ejes[0].set(xlabel="Tiempo (h)", ylabel="Tensión (V)", title="Descarga y ajuste por prueba")
    ejes[0].legend()
    auto[["medida_h", "calculada_h"]].rename(columns={"medida_h": "Medida", "calculada_h": "Calculada"}).plot.bar(ax=ejes[1], rot=0)
    ejes[1].set(ylabel="Horas", title="Autonomía del tramo continuo")
    guardar(fig, "r2_descarga_autonomia")

    bat = tabla.dropna(subset=["eficiencia_pct"])
    fig, ejes = plt.subplots(1, 2, figsize=(9, 4))
    bat[["p_sal_mW", "perdida_mW"]].rename(columns={"p_sal_mW": "A la carga", "perdida_mW": "Pérdida"}).plot.bar(stacked=True, ax=ejes[0], rot=0)
    ejes[0].set_ylabel("Potencia media (mW)")
    tabla.saltos.plot.bar(ax=ejes[1], rot=0, color="#df773a")
    ejes[1].set_ylabel("Saltos de tensión de entrada")
    guardar(fig, "r2_perdidas")

    fig, ejes = plt.subplots(1, 2, figsize=(10, 4))
    for pid, (nombre, fuente, archivo, d) in pruebas.items():
        e = energia(d.t, d.P)
        x = d.h.to_numpy()
        ejes[0].plot(x, e, "--", lw=0.9)
        ejes[0].plot(x, d.E_esp, lw=0.8, alpha=0.5, label=pid)
    ejes[0].set(xlabel="Tiempo (h)", ylabel="Energía de entrada (mWh)", title="Python (trazos) y ESP32 (líneas)")
    ejes[0].legend(ncol=2, fontsize=8)
    bat.eficiencia_pct.plot.bar(ax=ejes[1], rot=0, color="#004883", ylim=(0, 100))
    ejes[1].set(ylabel="Eficiencia (%)", title="Potencia de salida / entrada")
    guardar(fig, "r3_teorico_vs_real")

    fig, ax = plt.subplots(figsize=(8, 3.6))
    tabla.sigma_sal_mV.plot.bar(ax=ax, rot=0, color="#004883", logy=True)
    ax.set(ylabel="Desviación estándar (mV, log)", title="Estabilidad de la tensión de salida")
    guardar(fig, "r3_estabilidad")


def exportar(tabla, auto, raiz=RAIZ):
    carpeta = raiz / "tablas"
    carpeta.mkdir(exist_ok=True)
    numericas = tabla.drop(columns=["nombre", "archivo", "inicio"]).groupby("fuente")
    campos = ["v_ent_V", "i_ent_mA", "p_ent_mW", "v_sal_V", "i_sal_mA", "p_sal_mW", "sigma_sal_mV"]
    grupos = numericas[campos].mean()
    bat = tabla.dropna(subset=["eficiencia_pct"])
    tabla.round(4).to_csv(carpeta / "resumen_pruebas.csv", encoding="utf-8-sig")
    with pd.ExcelWriter(carpeta / "tablas_corte3.xlsx", engine="openpyxl") as libro:
        tabla.round(4).to_excel(libro, sheet_name="Resumen")
        grupos.round(4).to_excel(libro, sheet_name="Por fuente")
        bat[["eficiencia_pct", "perdida_mW", "p_ent_mW", "p_sal_mW"]].round(4).to_excel(libro, sheet_name="Rendimiento")
        auto.round(4).to_excel(libro, sheet_name="Autonomía")
    resultados = {
        "pruebas": json.loads(tabla.round(6).reset_index().to_json(orient="records")),
        "grupos": json.loads(grupos.round(6).to_json(orient="index")),
        "autonomia": json.loads(auto.round(6).reset_index().to_json(orient="records")),
        "total": {"lecturas": int(tabla.lecturas.sum()), "validas": int(tabla.validas.sum()),
                  "transcurridas_h": round(tabla.duracion_h.sum(), 4), "disponibles_h": round(tabla.horas_validas_h.sum(), 4),
                  "eficiencia_pct": round(bat.eficiencia_pct.mean(), 4), "perdida_mW": round(bat.perdida_mW.mean(), 4),
                  "error_energia_pct": round(tabla.error_energia_pct.mean(), 4), "error_potencia_pct": round(tabla.error_potencia_pct.mean(), 4),
                  "error_salida_pct": round(bat.error_salida_pct.mean(), 4), "saltos": int(tabla.saltos.sum())},
    }
    (raiz / "resultados.json").write_text(json.dumps(resultados, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf8")


def main():
    pruebas = preparar()
    tabla = resumen(pruebas)
    curvas, auto = modelos(pruebas, tabla)
    graficar(pruebas, tabla, curvas, auto, RAIZ / "graficas")
    exportar(tabla, auto)


if __name__ == "__main__":
    main()
