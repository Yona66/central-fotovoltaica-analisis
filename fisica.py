"""Funciones físicas, carga y limpieza de las medidas de la central fotovoltaica."""
import re
from pathlib import Path

import numpy as np
import openpyxl
import pandas as pd

RAIZ = Path(__file__).resolve().parent
DATOS = RAIZ / "datos"
COLS = ["n", "fecha", "t", "V", "I", "P_esp", "E_esp", "Vs", "Is", "Ps_esp", "Es_esp"]


# --- Ley de Ohm, potencia y energía (unidades: V, mA, mW, mWh, s, Ω) ---

def ohm_v(i_ma, r_ohm):
    return np.asarray(i_ma) / 1000 * r_ohm


def ohm_i(v, r_ohm):
    return np.asarray(v) / r_ohm * 1000


def ohm_r(v, i_ma):
    i = np.asarray(i_ma, dtype=float) / 1000
    return np.divide(v, i, out=np.full_like(i, np.nan), where=np.abs(i) > 1e-4)


def potencia(v, i_ma):
    return np.asarray(v) * np.asarray(i_ma)


def energia(t_s, p_mw):
    """Energía acumulada por trapecios; los huecos de más de 60 s no suman."""
    t, p = np.asarray(t_s, float), np.nan_to_num(np.asarray(p_mw, float))
    dt = np.diff(t, prepend=t[0])
    tramo = (p + np.roll(p, 1)) / 2 * dt / 3600
    tramo[0] = 0
    tramo[dt > 60] = 0
    return np.cumsum(tramo)


def eficiencia(p_sal, p_ent):
    return 100 * np.asarray(p_sal) / np.asarray(p_ent)


def error_pct(teorico, real):
    return 100 * np.abs(np.asarray(real) - np.asarray(teorico)) / np.abs(np.asarray(teorico))


# --- Carga de datos ---

def _tabla(hoja):
    filas = [r[:11] for r in hoja.iter_rows(min_row=3, values_only=True) if r[0] is not None]
    df = pd.DataFrame(filas, columns=COLS)
    df[COLS[2:]] = df[COLS[2:]].apply(pd.to_numeric, errors="coerce")
    return df


def leer_pruebas(archivo, nombre_archivo=None):
    """Cada hoja 'Prueba N' de cualquier Excel del ESP32 como (n, nombre, fuente, DataFrame)."""
    wb = openpyxl.load_workbook(archivo, read_only=True, data_only=True)
    hojas = [w for w in wb.worksheets if re.fullmatch(r"Prueba \d+", w.title)]
    if "Resumen" not in wb.sheetnames or not hojas:
        raise ValueError("no es un Excel de la página del ESP32 (faltan las hojas 'Resumen' y 'Prueba N')")
    res = [r for r in wb["Resumen"].iter_rows(min_row=2, values_only=True)]
    cab = [str(c or "") for c in res[0]]
    k = next((j for j, c in enumerate(cab) if c.startswith("Fuente")), None)
    info = {r[0]: (str(r[1] or ""), str(r[k] or "").lower() if k is not None else "") for r in res[1:] if r[0] is not None}
    arch = Path(nombre_archivo or archivo).name.lower()
    for w in hojas:
        n = int(w.title.split()[1])
        nombre, f = info.get(n, ("", ""))
        # Las pruebas de consumo son de noche y van con la batería, aunque en la página quedara "paneles".
        fuente = ("bateria" if "consumo" in nombre.lower() or "bater" in f or "bateria" in arch
                  else "paneles" if "panel" in f or "paneles" in arch or "Generaci" in nombre else "bateria")
        df = _tabla(w)
        df["h"] = df.t / 3600
        df["nombre"] = nombre
        yield n, nombre, fuente, df


def cargar(carpeta=DATOS):
    """Todas las pruebas de los Excel de la carpeta en una sola tabla."""
    tablas = [df.assign(prueba=n, fuente=fuente) for f in sorted(Path(carpeta).rglob("*.xlsx"))
              for n, _, fuente, df in leer_pruebas(f)]
    return pd.concat(tablas, ignore_index=True).sort_values(["prueba", "t"]).reset_index(drop=True)


# --- Limpieza ---

def limpiar(d, i_min=1.0):
    """Quita filas sin dato, con el sistema apagado o con corriente invertida."""
    ok = d[["V", "I", "Vs", "Is"]].notna().all(axis=1) & (d.I > i_min) & (d.Is > i_min)
    return d[ok].copy()


def mediana_movil(x, k=5):
    """Mediana de ventana k: quita picos sueltos sin desplazar los escalones."""
    x = np.asarray(x, float)
    r = k // 2
    pad = np.pad(x, r, mode="edge")
    return np.median(np.lib.stride_tricks.sliding_window_view(pad, k), axis=1)


def media_movil(x, k=12):
    """Promedio móvil centrado de k muestras (k=12 son 60 s)."""
    x = np.asarray(x, float)
    pad = np.pad(x, (k // 2, k - 1 - k // 2), mode="edge")
    return np.convolve(pad, np.ones(k) / k, mode="valid")


def filtrar(x, t=None, k_med=5, k_media=12, hueco=60):
    """Mediana y luego media móvil, por tramos: no promedia a través de huecos de más de 'hueco' s."""
    x = np.asarray(x, float)
    if t is None:
        return media_movil(mediana_movil(x, k_med), k_media)
    cortes = np.where(np.diff(np.asarray(t, float)) > hueco)[0] + 1
    return np.concatenate([media_movil(mediana_movil(s, k_med), k_media) for s in np.split(x, cortes) if len(s)])


def con_huecos(t, y, hueco=60):
    """Inserta NaN en cada hueco para que la gráfica corte la línea en vez de unir puntos lejanos."""
    t, y = np.asarray(t, float), np.asarray(y, float)
    k = np.where(np.diff(t) > hueco)[0] + 1
    return np.insert(t, k, np.nan), np.insert(y, k, np.nan)


# --- Detección de caídas de tensión ---

def caidas(t, v, i_ma, umbral=None, n_sigma=8):
    """Saltos bruscos de tensión entre muestras; R = ΔV/ΔI cuando la corriente también cambia."""
    v, i, t = np.asarray(v, float), np.asarray(i_ma, float), np.asarray(t, float)
    dv, di = np.diff(v), np.diff(i)
    if umbral is None:
        mad = np.nanmedian(np.abs(dv - np.nanmedian(dv))) * 1.4826  # nanmedian: un sensor caído no anula el umbral
        umbral = max(np.nan_to_num(n_sigma * mad), 0.05)
    k = np.where(np.abs(np.nan_to_num(dv)) > umbral)[0]
    with np.errstate(divide="ignore", invalid="ignore"):
        r = np.where(np.abs(di[k]) > 5, np.abs(dv[k] / (di[k] / 1000)), np.nan)
    return pd.DataFrame({"t_s": t[k + 1], "V_antes": v[k], "V_despues": v[k + 1], "dV": dv[k],
                         "I_antes": i[k], "I_despues": i[k + 1], "R_ohm": r})
