"""Visor web de las pruebas de la central fotovoltaica. Ejecutar: streamlit run app.py"""
import io

import altair as alt

import numpy as np
import pandas as pd
import streamlit as st

from analizar_prueba import comparar, estadistica, ficha
from fisica import DATOS, LOTE1, caidas, energia, filtrar, leer_pruebas, limpiar, potencia

st.set_page_config(page_title="Central fotovoltaica", page_icon="☀️", layout="wide")
FUENTES = ["paneles", "bateria", "carga"]
MAGNITUDES = {"Tensión (V)": ("V", "Vs"), "Corriente (mA)": ("I", "Is"), "Potencia (mW)": ("P", "Ps"),
              "Energía acumulada (mWh)": ("E", "Es")}


@st.cache_data
def leer(contenido, nombre):
    return list(leer_pruebas(io.BytesIO(contenido), nombre))


def preparar(d):
    d = d.assign(P=potencia(d.V, d.I), Ps=potencia(d.Vs, d.Is))
    return d.assign(E=energia(d.t, d.P), Es=energia(d.t, d.Ps))


def serie(ok, col, crudo):
    return ok[col].to_numpy() if crudo or col in ("E", "Es") else filtrar(ok[col], ok.t)


def detalle(n, fuente, d, ok, r_nom):
    comp, est, cai = comparar(d, ok, fuente, r_nom or None), estadistica(ok), caidas(ok.t, ok.Vs, ok.Is)
    k = st.columns(5)
    k[0].metric("Duración", f"{d.h.max():.2f} h")
    k[1].metric("Filas válidas", len(ok), help=f"{len(d) - len(ok)} descartadas de {len(d)}")
    k[2].metric("Energía entrada", f"{comp.Real[2]:.1f} mWh")
    k[3].metric("Energía salida", f"{comp.Real[3]:.1f} mWh")
    k[4].metric("Salida / entrada", f"{100 * comp.Real[3] / comp.Real[2]:.1f} %")

    g, tv, es, ca, da = st.tabs(["Gráficas", "Teórico vs real", "Estadística", "Caídas de tensión", "Datos"])
    with g:
        c1, c2 = st.columns([3, 1])
        mag = c1.radio("Magnitud", list(MAGNITUDES), horizontal=True)
        crudo = c2.toggle("Ver sin filtrar")
        a, b = MAGNITUDES[mag]
        tabla = pd.concat([pd.DataFrame({"h": ok.h, "valor": serie(ok, c, crudo), "nodo": nodo})
                           for c, nodo in ((a, "entrada"), (b, "salida"))])
        # Eje Y sin forzar el cero: si no, 3.9 V y 5.0 V se ven como líneas planas.
        graf = alt.Chart(tabla).mark_line().encode(
            x=alt.X("h:Q", title="Tiempo (h)"), y=alt.Y("valor:Q", title=mag, scale=alt.Scale(zero=False)),
            color=alt.Color("nodo:N", title=None, scale=alt.Scale(range=["#1f5fa8", "#e08a00"])))
        st.altair_chart(graf.interactive(), width="stretch")
        st.caption("Filtro: mediana de 5 muestras (quita picos) y media móvil de 60 s (suaviza). "
                   "Arrastra para mover y usa la rueda para hacer zoom.")
    with tv:
        st.dataframe(comp, hide_index=True, width="stretch")
        st.caption("Error = |real − teórico| / |teórico| · 100. La eficiencia solo se calcula si la fuente es la batería.")
    with es:
        st.dataframe(est, width="stretch")
        st.caption("Desviación estándar con NumPy: mide qué tan estable es cada magnitud.")
    with ca:
        st.write(f"**{len(cai)}** saltos bruscos de tensión en la salida.")
        st.dataframe(cai.round(3), hide_index=True, width="stretch")
    with da:
        st.dataframe(ok.drop(columns=["fecha"]).round(3), hide_index=True, width="stretch")
    buf = io.BytesIO()
    ficha(buf, comp, est, cai, ok)
    st.download_button("Descargar ficha en Excel", buf.getvalue(), f"ficha_P{n}.xlsx")


# --- Barra lateral: de dónde salen los datos ---
st.sidebar.title("☀️ Central fotovoltaica")
subidos = st.sidebar.file_uploader("Excel descargados de la página del ESP32", type="xlsx", accept_multiple_files=True)
archivos = [(f.getvalue(), f.name, False) for f in subidos or []]
if st.sidebar.checkbox("Incluir las pruebas del proyecto", value=not archivos):
    archivos += [(p.read_bytes(), p.name, p.parent == DATOS) for p in sorted(DATOS.rglob("*.xlsx"))]
r_nom = st.sidebar.number_input("Resistencia de la carga (Ω) para comparar con Ohm; 0 = no comparar",
                                min_value=0.0, value=0.0, step=10.0)

pruebas = {}
for contenido, nombre, lote1 in archivos:
    try:
        for n, nom, fuente, d in leer(contenido, nombre):
            if lote1 and n in LOTE1:  # mismo recorte que el notebook: después el sensor se movió
                fuente, t_max = LOTE1[n]
                d = d[d.t < t_max]
            pruebas[f"P{n} · {nom or nombre}"] = (n, nom, fuente, preparar(d))
    except Exception as e:  # un archivo malo no detiene los demás
        st.sidebar.error(f"{nombre}: no se pudo leer ({e})")
if not pruebas:
    st.info("Sube uno o varios Excel del ESP32 en la barra de la izquierda.")
    st.stop()

una, todas = st.tabs(["Una prueba", "Todas las pruebas"])

with una:
    clave = st.selectbox("Prueba", sorted(pruebas, key=lambda k: pruebas[k][0]))
    n, nom, fuente, d = pruebas[clave]
    fuente = st.radio("Fuente de energía (los Excel viejos no la traen)", FUENTES, index=FUENTES.index(fuente),
                      horizontal=True, key=f"fuente_{clave}")
    ok = limpiar(d)
    if len(ok) < 10:
        st.warning(f"Solo {len(ok)} filas válidas: no alcanza para analizar.")
    else:
        detalle(n, fuente, d, ok, r_nom)

with todas:
    filas = []
    for clave, (n, nom, fuente, d) in pruebas.items():
        ok = limpiar(d)
        if len(ok) < 10:
            continue
        e_ent, e_sal = d.E.iat[-1], d.Es.iat[-1]
        filas.append({"Prueba": clave, "Fuente": fuente, "Duración (h)": d.h.max(), "Filas válidas": len(ok),
                      "E entrada (mWh)": e_ent, "E salida (mWh)": e_sal, "Salida / entrada (%)": 100 * e_sal / e_ent,
                      "V salida media (V)": ok.Vs.mean(), "σ V salida (mV)": 1000 * np.std(ok.Vs)})
    resumen = pd.DataFrame(filas).sort_values(["Fuente", "Prueba"]).round(2)
    st.subheader("Clasificación por fuente de energía")
    st.dataframe(resumen, hide_index=True, width="stretch")
    st.bar_chart(resumen, x="Prueba", y="E entrada (mWh)", color="Fuente", y_label="Energía de entrada (mWh)")
    st.download_button("Descargar resumen (CSV)", resumen.to_csv(index=False).encode("utf-8-sig"), "resumen_pruebas.csv")
