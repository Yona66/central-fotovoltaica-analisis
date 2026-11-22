"""Visor web de las pruebas de la central fotovoltaica. Ejecutar: streamlit run app.py"""
import io
from pathlib import Path

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st

from analizar_prueba import comparar, estadistica, ficha
from fisica import DATOS, LOTE1, caidas, energia, filtrar, leer_pruebas, limpiar, potencia

st.set_page_config(page_title="Central fotovoltaica", page_icon="☀️", layout="wide")
st.html(f"<style>{(Path(__file__).parent / 'estilo.css').read_text(encoding='utf-8')}</style>")

FUENTES = ["paneles", "bateria", "carga"]
COLOR = {"paneles": "#b45309", "bateria": "#1f5fa8", "carga": "#0f766e", "entrada": "#1f5fa8", "salida": "#d97706"}
MAGNITUDES = {"Tensión": ("V", "Vs", "V"), "Corriente": ("I", "Is", "mA"), "Potencia": ("P", "Ps", "mW"),
              "Energía acumulada": ("E", "Es", "mWh")}
_I = {  # iconos de trazo (24x24), toman el color del texto
    "reloj": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "filas": '<path d="M4 6h16M4 12h16M4 18h10"/>',
    "sol": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',
    "bateria": '<rect x="2" y="7" width="17" height="10" rx="2"/><path d="M22 11v2M6 11v2M10 11v2"/>',
    "carga": '<path d="M12 22v-5M9 8V2M15 8V2M18 8v4a6 6 0 0 1-12 0V8z"/>',
    "rayo": '<path d="M13 2 4 14h8l-1 8 9-12h-8z"/>',
    "eficiencia": '<path d="M19 5 5 19"/><circle cx="6.5" cy="6.5" r="2.5"/><circle cx="17.5" cy="17.5" r="2.5"/>',
}
ICONO_FUENTE = {"paneles": "sol", "bateria": "bateria", "carga": "carga"}


def icono(nombre):
    return (f'<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{_I[nombre]}</svg>')


def insignia(fuente):
    c = COLOR[fuente]
    return (f'<span class="fuente" style="color:{c};background:color-mix(in oklch,{c} 12%,white)">'
            f'{icono(ICONO_FUENTE[fuente])}{fuente}</span>')


def kpi(ico, etiqueta, valor, unidad="", pie="", color=None):
    c = f' style="--c:{color}"' if color else ""
    return (f'<div class="kpi"{c}><div class="ico">{icono(ico)}</div><div class="et">{etiqueta}</div>'
            f'<div class="v">{valor}<small>{unidad}</small></div><div class="pie">{pie}</div></div>')


@st.cache_data
def leer(contenido, nombre):
    return list(leer_pruebas(io.BytesIO(contenido), nombre))


def preparar(d):
    d = d.assign(P=potencia(d.V, d.I), Ps=potencia(d.Vs, d.Is))
    return d.assign(E=energia(d.t, d.P), Es=energia(d.t, d.Ps))


@alt.theme.register("central", enable=True)
def tema():
    return alt.theme.ThemeConfig({"config": {
        "background": "transparent", "view": {"stroke": None},
        "font": "Source Sans Pro, Segoe UI, sans-serif",
        "axis": {"labelColor": "#64748b", "titleColor": "#334155", "gridColor": "#e8edf3", "domain": False,
                 "tickColor": "#e8edf3", "labelFontSize": 12, "titleFontSize": 13, "titleFontWeight": 600},
        "legend": {"labelColor": "#334155", "titleColor": "#334155", "orient": "top", "labelFontSize": 13},
    }})


def grafica(ok, mag, crudo):
    a, b, u = MAGNITUDES[mag]
    acumulada = a == "E"
    filas = []
    for col, nodo in ((a, "entrada"), (b, "salida")):
        y = ok[col].to_numpy()
        filas.append(pd.DataFrame({"h": ok.h, "valor": y if acumulada else filtrar(y, ok.t), "nodo": nodo, "capa": "filtrada"}))
        if crudo and not acumulada:
            filas.append(pd.DataFrame({"h": ok.h, "valor": y, "nodo": nodo, "capa": "medida"}))
    tabla = pd.concat(filas)
    color = alt.Color("nodo:N", title=None, scale=alt.Scale(domain=["entrada", "salida"],
                                                            range=[COLOR["entrada"], COLOR["salida"]]))
    x = alt.X("h:Q", title="Tiempo (h)", scale=alt.Scale(domain=[0, float(ok.h.max())], nice=False))
    # Eje Y sin forzar el cero: si no, 3.9 V y 5.0 V se ven como líneas planas.
    y = alt.Y("valor:Q", title=f"{mag} ({u})", scale=alt.Scale(zero=False))
    base = alt.Chart(tabla).encode(x=x, y=y, color=color)
    cerca = alt.selection_point(nearest=True, on="pointerover", fields=["h"], empty=False, clear="pointerout")
    zoom = alt.selection_interval(bind="scales", encodings=["x"])
    capas = []
    if crudo and not acumulada:
        capas.append(base.transform_filter("datum.capa == 'medida'").mark_line(strokeWidth=1, opacity=0.25))
    filtrada = base.transform_filter("datum.capa == 'filtrada'")
    capas += [
        filtrada.mark_line(strokeWidth=2.2).add_params(zoom),
        filtrada.mark_point(filled=True, size=70).encode(
            opacity=alt.condition(cerca, alt.value(1), alt.value(0)),
            tooltip=[alt.Tooltip("nodo:N", title="Nodo"), alt.Tooltip("h:Q", title="Tiempo (h)", format=".2f"),
                     alt.Tooltip("valor:Q", title=f"{mag} ({u})", format=".3f")]).add_params(cerca),
        alt.Chart(tabla).mark_rule(color="#94a3b8", strokeDash=[4, 4]).encode(x="h:Q").transform_filter(cerca),
    ]
    return alt.layer(*capas).properties(height=420)


def color_error(v):
    if pd.isna(v):
        return ""
    c, f = ("#15803d", "#dcfce7") if v < 1 else ("#a16207", "#fef3c7") if v < 5 else ("#b91c1c", "#fee2e2")
    return f"color: {c}; background-color: {f}; font-weight: 600"


def detalle(n, nom, fuente, d, ok, r_nom):
    comp, est, cai = comparar(d, ok, fuente, r_nom or None), estadistica(ok), caidas(ok.t, ok.Vs, ok.Is)
    e_ent, e_sal = comp.Real[2], comp.Real[3]
    rel = 100 * e_sal / e_ent
    st.markdown('<div class="kpis">' + "".join([
        kpi("reloj", "Duración", f"{d.h.max():.2f}", " h", f"{len(d)} lecturas"),
        kpi("filas", "Filas válidas", f"{len(ok)}", "", f"{len(d) - len(ok)} descartadas"),
        kpi(ICONO_FUENTE[fuente], "Energía de entrada", f"{e_ent:,.1f}", " mWh", fuente, COLOR[fuente]),
        kpi("rayo", "Energía de salida", f"{e_sal:,.1f}", " mWh", "MT3608 a 5 V", COLOR["salida"]),
        kpi("eficiencia", "Salida / entrada", f"{rel:.1f}", " %", f"se pierden {e_ent - e_sal:,.1f} mWh", "#0f766e"),
    ]) + "</div>", unsafe_allow_html=True)

    g, tv, es, ca, da = st.tabs(["Gráficas", "Teórico vs real", "Estadística", "Caídas de tensión", "Datos"])
    with g:
        c1, c2 = st.columns([4, 1.4], vertical_alignment="center")
        mag = c1.segmented_control("Magnitud", list(MAGNITUDES), default="Tensión", label_visibility="collapsed")
        crudo = c2.toggle("Ver medida sin filtrar", help="Línea clara de fondo con las lecturas tal cual.")
        st.altair_chart(grafica(ok, mag or "Tensión", crudo), width="stretch", theme=None)
        st.markdown('<p class="nota">Filtro: mediana de 5 muestras (quita picos) y media móvil de 60 s (suaviza). '
                    'Pasa el puntero para leer valores; arrastra o usa la rueda para acercar en el tiempo; '
                    'doble clic para volver.</p>', unsafe_allow_html=True)
    with tv:
        st.dataframe(comp.style.map(color_error, subset=["Error (%)"]).format(
            {"Teórico": "{:,.3f}", "Real": "{:,.3f}", "Error (%)": "{:.2f} %"}), hide_index=True, width="stretch")
        st.markdown('<p class="nota">Error = |real − teórico| / |teórico| · 100. Verde menos de 1 %, ámbar menos '
                    'de 5 %, rojo 5 % o más. La eficiencia solo se calcula con la batería como fuente.</p>',
                    unsafe_allow_html=True)
    with es:
        st.dataframe(est.style.format("{:,.3f}"), width="stretch")
        st.markdown('<p class="nota">Desviación estándar con NumPy: cuanto más baja, más estable.</p>',
                    unsafe_allow_html=True)
    with ca:
        st.markdown(f'<p class="seccion">{len(cai)} saltos bruscos de tensión en la salida</p>', unsafe_allow_html=True)
        if len(cai):
            st.dataframe(cai.round(3), hide_index=True, width="stretch")
        else:
            st.markdown('<p class="nota">Ninguno: la salida se mantuvo estable en toda la prueba.</p>',
                        unsafe_allow_html=True)
    with da:
        st.dataframe(ok.drop(columns=["fecha"]).round(3), hide_index=True, width="stretch", height=420)
    buf = io.BytesIO()
    ficha(buf, comp, est, cai, ok)
    st.download_button("Descargar ficha en Excel", buf.getvalue(), f"ficha_P{n}.xlsx", icon=":material/download:")


def resumen_todas(pruebas):
    filas = []
    for clave, (n, nom, fuente, d) in pruebas.items():
        ok = limpiar(d)
        if len(ok) < 10:
            continue
        e_ent, e_sal = d.E.iat[-1], d.Es.iat[-1]
        filas.append({"Prueba": f"P{n}", "Nombre": nom or "—", "Fuente": fuente, "Duración (h)": d.h.max(),
                      "Filas válidas": len(ok), "E entrada (mWh)": e_ent, "E salida (mWh)": e_sal,
                      "Salida / entrada (%)": 100 * e_sal / e_ent, "V salida media (V)": ok.Vs.mean(),
                      "σ V salida (mV)": 1000 * np.std(ok.Vs)})
    r = pd.DataFrame(filas)
    r["n"] = r.Prueba.str[1:].astype(int)
    return r.sort_values(["Fuente", "n"]).drop(columns="n")


def barras(r, campo, titulo):
    escala = alt.Scale(domain=FUENTES, range=[COLOR[f] for f in FUENTES])
    return alt.Chart(r).mark_bar(cornerRadiusEnd=4, height=16).encode(
        y=alt.Y("Prueba:N", sort="-x", title=None),
        x=alt.X(f"{campo}:Q", title=titulo),
        color=alt.Color("Fuente:N", scale=escala, title=None),
        tooltip=["Prueba", "Nombre", "Fuente", alt.Tooltip(f"{campo}:Q", format=",.1f")],
    ).properties(height=max(220, 30 * len(r)))


# --- Barra lateral: de dónde salen los datos ---
with st.sidebar:
    st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">'
                f'<span style="color:#d97706;width:28px;height:28px;display:inline-block">{icono("sol")}</span>'
                f'<b style="font-size:20px">Central fotovoltaica</b></div>', unsafe_allow_html=True)
    st.caption("Analítica de las pruebas registradas por el ESP32")
    subidos = st.file_uploader("Excel descargados de la página del ESP32", type="xlsx", accept_multiple_files=True)
    archivos = [(f.getvalue(), f.name, False) for f in subidos or []]
    if st.toggle("Incluir las pruebas del proyecto", value=not archivos):
        archivos += [(p.read_bytes(), p.name, p.parent == DATOS) for p in sorted(DATOS.rglob("*.xlsx"))]
    r_nom = st.number_input("Resistencia de la carga (Ω)", min_value=0.0, value=0.0, step=10.0,
                            help="Con un valor mayor que 0 se compara la corriente medida con la ley de Ohm.")

pruebas, malos = {}, []
with st.spinner("Leyendo los Excel…"):
    for contenido, nombre, lote1 in archivos:
        try:
            for n, nom, fuente, d in leer(contenido, nombre):
                if lote1 and n in LOTE1:  # mismo recorte que el notebook: después el sensor se movió
                    fuente, t_max = LOTE1[n]
                    d = d[d.t < t_max]
                pruebas[f"P{n} · {nom or nombre}"] = (n, nom, fuente, preparar(d))
        except Exception as e:  # un archivo malo no detiene los demás
            malos.append(f"**{nombre}**: no se pudo leer ({e})")
for m in malos:
    st.sidebar.error(m, icon=":material/error:")

cuenta = {f: sum(p[2] == f for p in pruebas.values()) for f in FUENTES}
st.markdown(
    '<div class="hero entra"><p class="eti">Monitoreo · análisis en Python</p>'
    '<h1>Central fotovoltaica</h1>'
    '<p>Medidas reales de los sensores INA260: entrada (paneles o batería) y salida del elevador MT3608.</p>'
    '<div class="chips">' + f'<span>{len(pruebas)} pruebas</span>' +
    "".join(f'<span>{icono(ICONO_FUENTE[f])}{cuenta[f]} {f}</span>' for f in FUENTES if cuenta[f]) +
    "</div></div>", unsafe_allow_html=True)

if not pruebas:
    st.info("Sube uno o varios Excel del ESP32 en la barra de la izquierda.", icon=":material/upload_file:")
    st.stop()

una, todas = st.tabs([":material/monitoring: Una prueba", ":material/table_chart: Todas las pruebas"])

with una:
    c1, c2 = st.columns([3, 2], vertical_alignment="bottom")
    clave = c1.selectbox("Prueba", sorted(pruebas, key=lambda k: pruebas[k][0]))
    n, nom, fuente, d = pruebas[clave]
    fuente = c2.segmented_control("Fuente de energía", FUENTES, default=fuente, key=f"fuente_{clave}",
                                  help="Los Excel viejos no la traen: corrígela aquí si hace falta.") or fuente
    ok = limpiar(d)
    if len(ok) < 10:
        st.warning(f"Solo {len(ok)} filas válidas: no alcanza para analizar esta prueba.", icon=":material/warning:")
    else:
        detalle(n, nom, fuente, d, ok, r_nom)

with todas:
    r = resumen_todas(pruebas)
    st.markdown('<p class="seccion">Clasificación por fuente de energía</p>', unsafe_allow_html=True)
    st.markdown(" ".join(insignia(f) + f' <span class="nota">{cuenta[f]}</span>&nbsp;&nbsp;' for f in FUENTES if cuenta[f]),
                unsafe_allow_html=True)
    st.dataframe(r.style.format({c: "{:,.2f}" for c in r.columns if r[c].dtype.kind == "f"}),
                 hide_index=True, width="stretch", height=35 * (len(r) + 1) + 3)
    g1, g2 = st.columns(2)
    g1.markdown('<p class="seccion">Energía que entró en cada prueba</p>', unsafe_allow_html=True)
    g2.markdown('<p class="seccion">Cuánto de esa energía llegó a la salida</p>', unsafe_allow_html=True)
    g1.altair_chart(barras(r, "E entrada (mWh)", "Energía de entrada (mWh)"), width="stretch", theme=None)
    g2.altair_chart(barras(r, "Salida / entrada (%)", "Salida / entrada (%)"), width="stretch", theme=None)
    st.download_button("Descargar resumen (CSV)", r.to_csv(index=False).encode("utf-8-sig"), "resumen_pruebas.csv",
                       icon=":material/download:")
