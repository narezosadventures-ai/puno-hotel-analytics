from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==================================================
# 1. CONFIGURACION GENERAL
# ==================================================

st.set_page_config(
    page_title="Business Analytics | Hoteles Puno",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded",
)

CARPETA = Path(__file__).resolve().parent
ARCHIVO = CARPETA / "hoteles_puno_validado.csv"

MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre",
}
MESES_CORTO = {k: v[:3] for k, v in MESES.items()}

NAVY = "#0B2545"
AZUL = "#13315C"
CELESTE = "#1D4E89"
VERDE = "#00A6A6"
NARANJA = "#E0A458"
ROJO = "#C8553D"
MORADO = "#7A5C99"
GRIS = "#5B6B82"
PALETA = [CELESTE, VERDE, NARANJA, MORADO, ROJO, "#2D936C", "#4C6A92"]

# Los archivos 2019-2023 usan codigos y los de 2024-2025 usan nombres.
# Se unifican para poder comparar todos los años.
MAP_CLASE = {
    "00": "NO CLASIFICADO", "01": "HOTEL", "03": "HOSTAL",
    "05": "ALBERGUE", "TT": "TODAS", "TODAS CONSOLIDADAS": "TODAS",
}
MAP_CATEGORIA = {
    "00": "NO CATEGORIZADO", "01": "1 ESTRELLA", "02": "2 ESTRELLAS",
    "03": "3 ESTRELLAS", "04": "4 ESTRELLAS", "05": "5 ESTRELLAS",
    "12": "ALBERGUE", "TT": "TODAS", "TODAS CONSOLIDADAS": "TODAS",
}

# ==================================================
# 2. ESTILOS
# ==================================================

st.markdown(
    f"""
<style>
.block-container {{ padding-top: 1.2rem; padding-bottom: 2rem; max-width: 1450px; }}
#MainMenu, footer {{ visibility: hidden; }}
.stApp {{ background: #F4F6FA; }}

/* ---------- Barra lateral oscura ---------- */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {NAVY} 0%, {AZUL} 100%);
}}
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] label p,
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
[data-testid="stSidebar"] [data-testid="stSliderThumbValue"],
[data-testid="stSidebar"] [data-testid="stTickBarMin"],
[data-testid="stSidebar"] [data-testid="stTickBarMax"] {{
    color: #FFFFFF !important;
}}
[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,.18); }}
.sb-sec {{
    color: {NARANJA}; font-weight: 700; font-size: .8rem; letter-spacing: .08em;
    text-transform: uppercase; margin: 14px 0 2px 0;
}}

/* ---------- Cabecera ---------- */
.hero {{
    background: linear-gradient(120deg, {NAVY} 0%, {AZUL} 55%, {CELESTE} 100%);
    padding: 26px 32px; border-radius: 16px; color: white; margin-bottom: 18px;
    border-bottom: 4px solid {NARANJA};
}}
.hero h1 {{ color: white; margin: 0; font-size: 1.9rem; }}
.hero p {{ margin: 6px 0 0 0; opacity: .88; font-size: .95rem; }}

/* ---------- Tarjetas ---------- */
.kpi {{
    background: white; border: 1px solid #E1E7F0; border-top: 4px solid {CELESTE};
    border-radius: 12px; padding: 14px 18px; box-shadow: 0 2px 8px rgba(11,37,69,.07);
    height: 100%;
}}
.kpi .t {{ color: {GRIS}; font-size: .76rem; text-transform: uppercase; letter-spacing: .05em; }}
.kpi .v {{ color: {NAVY}; font-size: 1.65rem; font-weight: 700; line-height: 1.25; }}
.kpi .d {{ font-size: .82rem; font-weight: 600; }}
.up {{ color: #1E9E62; }} .down {{ color: {ROJO}; }} .flat {{ color: {GRIS}; }}

.insight {{
    background: white; border: 1px solid #E1E7F0; border-left: 4px solid {NARANJA};
    border-radius: 10px; padding: 10px 14px; margin-bottom: 8px; color: {NAVY}; font-size: .93rem;
}}
h2, h3 {{ color: {NAVY}; }}
button[data-baseweb="tab"] {{ font-weight: 600; }}
</style>
""",
    unsafe_allow_html=True,
)

# ==================================================
# 3. CARGA Y LIMPIEZA
# ==================================================


@st.cache_data
def cargar_datos(ruta, fecha_modificacion):
    datos = pd.read_csv(
        ruta, encoding="utf-8-sig", low_memory=False,
        dtype={"CLASE": str, "CATEGORIA": str},
    )
    datos.columns = [c.strip().upper() for c in datos.columns]

    obligatorias = ["ANIO", "MES", "CLASE", "CATEGORIA", "ARRIBOS", "PERNOCTACIONES"]
    faltantes = [c for c in obligatorias if c not in datos.columns]
    if faltantes:
        raise ValueError(f"Faltan columnas: {faltantes}")

    numericas = [
        "ANIO", "MES", "ESTABLECIMIENTOS", "HABITACIONES", "PLAZAS_CAMA",
        "TNOH", "TNOC", "ARRIBOS", "ARRIBOS_NAC", "ARRIBOS_EXT",
        "PERNOCTACIONES", "EMPLEO",
    ]
    for c in numericas:
        if c in datos.columns:
            datos[c] = pd.to_numeric(
                datos[c].astype(str).str.strip().str.replace(",", ".", regex=False),
                errors="coerce",
            )

    datos = datos.dropna(subset=["ANIO", "MES"])
    datos["ANIO"] = datos["ANIO"].astype(int)
    datos["MES"] = datos["MES"].astype(int)
    datos = datos[datos["MES"].between(1, 12)].copy()

    datos["CLASE_N"] = datos["CLASE"].str.strip().str.upper().map(MAP_CLASE)
    datos["CATEGORIA_N"] = datos["CATEGORIA"].str.strip().str.upper().map(MAP_CATEGORIA)
    datos = datos.dropna(subset=["CLASE_N", "CATEGORIA_N"])

    datos["NOMBRE_MES"] = datos["MES"].map(MESES)
    datos["FECHA"] = pd.to_datetime(
        dict(year=datos["ANIO"], month=datos["MES"], day=1)
    )
    return datos


if not ARCHIVO.exists():
    st.error("No se encontró hoteles_puno_validado.csv en la carpeta del proyecto.")
    st.stop()

try:
    df = cargar_datos(str(ARCHIVO), ARCHIVO.stat().st_mtime)
except Exception as error:
    st.error(f"Error al cargar datos: {error}")
    st.stop()

if df.empty:
    st.error("La base de datos no contiene registros válidos.")
    st.stop()

# ==================================================
# 4. PANEL LATERAL (FILTROS)
# ==================================================
# IMPORTANTE: la base mezcla varios niveles de agregacion (total, clase,
# categoria). Para no duplicar cifras, cada seleccion usa UNA sola fila
# por mes: el total departamental o la combinacion clase-categoria elegida.

st.sidebar.title("🏨 Panel de control")
st.sidebar.caption("Business Analytics · Puno")

anios_disp = sorted(df["ANIO"].unique().tolist())
anios_completos = [
    a for a in anios_disp if df.loc[df["ANIO"] == a, "MES"].nunique() == 12
]
ultimo_completo = max(anios_completos) if anios_completos else anios_disp[-1]

PRESETS = {
    "Personalizado": None,
    "Todo el periodo": anios_disp,
    "Pre-pandemia (2019)": [2019],
    "Pandemia (2020-2021)": [2020, 2021],
    "Recuperación (2022-2024)": [2022, 2023, 2024],
    f"Último año completo ({ultimo_completo})": [ultimo_completo],
}

# ---- Periodo ----
st.sidebar.markdown('<div class="sb-sec">📅 Periodo</div>', unsafe_allow_html=True)
preset = st.sidebar.selectbox("Periodo rápido", list(PRESETS.keys()))
anios_custom = st.sidebar.multiselect(
    "Años", anios_disp, default=anios_disp,
    disabled=PRESETS[preset] is not None,
    help="2025 contiene solo enero-junio.",
)
if PRESETS[preset] is not None:
    anios_sel = [a for a in PRESETS[preset] if a in anios_disp]
else:
    anios_sel = anios_custom
if not anios_sel:
    st.warning("Selecciona al menos un año.")
    st.stop()

mes_ini, mes_fin = st.sidebar.select_slider(
    "Rango de meses",
    options=list(MESES.keys()),
    value=(1, 12),
    format_func=lambda m: MESES_CORTO[m],
)
meses_sel = list(range(mes_ini, mes_fin + 1))

# ---- Segmento ----
st.sidebar.markdown('<div class="sb-sec">🏷️ Segmento</div>', unsafe_allow_html=True)
clases = ["TODAS"] + sorted(c for c in df["CLASE_N"].unique() if c != "TODAS")
clase_sel = st.sidebar.selectbox(
    "Tipo de alojamiento", clases,
    format_func=lambda x: "Todos" if x == "TODAS" else x.title(),
)
cats_disp = df.loc[df["CLASE_N"] == clase_sel, "CATEGORIA_N"].unique().tolist()
cats_disp = ["TODAS"] + sorted(c for c in cats_disp if c != "TODAS")
cat_sel = st.sidebar.selectbox(
    "Categoría", cats_disp,
    format_func=lambda x: "Todas" if x == "TODAS" else x.title(),
)

# ---- Visualizacion ----
st.sidebar.markdown('<div class="sb-sec">📊 Visualización</div>', unsafe_allow_html=True)
metrica = st.sidebar.radio(
    "Indicador para los gráficos",
    ["ARRIBOS", "PERNOCTACIONES"],
    format_func=lambda x: x.title(),
    horizontal=True,
)
tipo_grafico = st.sidebar.radio(
    "Tipo de gráfico (serie mensual)", ["Línea", "Barras", "Área"], horizontal=True
)
media_movil = st.sidebar.checkbox("Mostrar media móvil de 3 meses", value=True)
base_comp = st.sidebar.selectbox(
    "Comparar tarjetas contra", ["Año anterior", "Año 2019 (pre-pandemia)", "Sin comparación"]
)

# ---- Metas ----
st.sidebar.markdown('<div class="sb-sec">🎯 Metas</div>', unsafe_allow_html=True)
meta_tnoh = st.sidebar.slider("Meta de ocupación de habitaciones (%)", 10, 60, 30)
meta_estancia = st.sidebar.slider("Meta de estancia (noches)", 1.0, 3.0, 1.5, 0.1)

st.sidebar.divider()
st.sidebar.info(
    "Fuente declarada: MINCETUR · Cobertura 2019-2025. "
    "El año 2025 es parcial (enero-junio)."
)

# Serie mensual para la seleccion (una fila por año-mes)
serie_base = df[(df["CLASE_N"] == clase_sel) & (df["CATEGORIA_N"] == cat_sel)].copy()

if serie_base.empty:
    st.warning("No hay registros para esa combinación de tipo y categoría.")
    st.stop()

serie_base = serie_base.drop_duplicates(subset=["ANIO", "MES"])
serie_filtrada = serie_base[
    serie_base["ANIO"].isin(anios_sel) & serie_base["MES"].isin(meses_sel)
].sort_values("FECHA")

if serie_filtrada.empty:
    st.warning("No hay datos para los filtros elegidos.")
    st.stop()

st.sidebar.caption(f"Meses con datos: {len(serie_filtrada):,}")

# ==================================================
# 5. FUNCIONES AUXILIARES
# ==================================================


def formato(valor, decimales=0, sufijo=""):
    if valor is None or pd.isna(valor):
        return "N/D"
    return f"{valor:,.{decimales}f}{sufijo}"


def periodo_anterior(datos, anios, meses, modo):
    """Mismos meses de un año de referencia (solo si se eligio un unico año)."""
    if len(anios) != 1 or modo == "Sin comparación":
        return None
    ref = anios[0] - 1 if modo == "Año anterior" else 2019
    if ref == anios[0]:
        return None
    previo = datos[(datos["ANIO"] == ref) & (datos["MES"].isin(meses))]
    if previo["MES"].nunique() != len(meses):
        return None
    return previo


def variacion(actual, anterior):
    if anterior is None or pd.isna(anterior) or anterior == 0:
        return None
    return (actual / anterior - 1) * 100


def tarjeta(titulo, valor, delta=None, color=CELESTE, bueno_si_sube=True, ref="año anterior"):
    if delta is None:
        d_html = '<div class="d flat">&nbsp;</div>'
    else:
        flecha = "▲" if delta > 0 else ("▼" if delta < 0 else "■")
        sube = delta > 0
        clase = "flat" if delta == 0 else ("up" if sube == bueno_si_sube else "down")
        d_html = f'<div class="d {clase}">{flecha} {abs(delta):.1f}% vs {ref}</div>'
    st.markdown(
        f'<div class="kpi" style="border-top-color:{color}">'
        f'<div class="t">{titulo}</div><div class="v">{valor}</div>{d_html}</div>',
        unsafe_allow_html=True,
    )


def estilo(fig, alto=420):
    fig.update_layout(
        template="plotly_white",
        height=alto,
        colorway=PALETA,
        margin=dict(l=10, r=10, t=55, b=10),
        font=dict(family="Segoe UI, Arial", size=13, color=AZUL),
        title=dict(font=dict(size=16, color=AZUL)),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
        hoverlabel=dict(bgcolor="white"),
    )
    return fig


def grafico(fig):
    st.plotly_chart(fig, width="stretch")


def insight(texto):
    st.markdown(f'<div class="insight">💡 {texto}</div>', unsafe_allow_html=True)


# ==================================================
# 6. CABECERA
# ==================================================

nombre_nivel = (
    "Total departamental"
    if clase_sel == "TODAS" and cat_sel == "TODAS"
    else f"{'Todos' if clase_sel == 'TODAS' else clase_sel.title()}"
    f" · {'todas las categorías' if cat_sel == 'TODAS' else cat_sel.lower()}"
)

st.markdown(
    f"""
<div class="hero">
  <h1>🏨 Business Analytics · Hoteles de Puno</h1>
  <p>Actividad hotelera 2019–2025 · {nombre_nivel} ·
     {MESES[mes_ini]}–{MESES[mes_fin]} · Universidad Nacional del Altiplano</p>
</div>
""",
    unsafe_allow_html=True,
)

# ==================================================
# 7. INDICADORES (KPIs)
# ==================================================

arribos = serie_filtrada["ARRIBOS"].sum()
pernoc = serie_filtrada["PERNOCTACIONES"].sum()
estancia = pernoc / arribos if arribos else None
nac = serie_filtrada["ARRIBOS_NAC"].sum() if "ARRIBOS_NAC" in serie_filtrada else None
ext = serie_filtrada["ARRIBOS_EXT"].sum() if "ARRIBOS_EXT" in serie_filtrada else None
pct_ext = ext / (nac + ext) * 100 if nac is not None and (nac + ext) > 0 else None
tnoh = serie_filtrada["TNOH"].mean()
estab = serie_filtrada["ESTABLECIMIENTOS"].mean()

prev = periodo_anterior(serie_base, anios_sel, meses_sel, base_comp)
ref_txt = "año anterior" if base_comp == "Año anterior" else "2019"
d_arr = d_per = d_est = d_ext = d_tnoh = None
if prev is not None:
    d_arr = variacion(arribos, prev["ARRIBOS"].sum())
    d_per = variacion(pernoc, prev["PERNOCTACIONES"].sum())
    p_est = prev["PERNOCTACIONES"].sum() / prev["ARRIBOS"].sum() if prev["ARRIBOS"].sum() else None
    d_est = variacion(estancia, p_est) if estancia and p_est else None
    d_tnoh = variacion(tnoh, prev["TNOH"].mean())
    if ext is not None and prev["ARRIBOS_EXT"].sum():
        d_ext = variacion(ext, prev["ARRIBOS_EXT"].sum())

k1, k2, k3, k4, k5, k6 = st.columns(6)
with k1:
    tarjeta("Arribos", formato(arribos), d_arr, CELESTE, ref=ref_txt)
with k2:
    tarjeta("Pernoctaciones", formato(pernoc), d_per, VERDE, ref=ref_txt)
with k3:
    tarjeta("Estancia promedio", formato(estancia, 2, " noches"), d_est, NARANJA, ref=ref_txt)
with k4:
    tarjeta("Ocupación hab. (TNOH)", formato(tnoh, 1, "%"), d_tnoh, MORADO, ref=ref_txt)
with k5:
    tarjeta("Arribos extranjeros", formato(ext), d_ext, ROJO, ref=ref_txt)
with k6:
    tarjeta("% extranjeros", formato(pct_ext, 1, "%"), None, GRIS)

if prev is None and len(anios_sel) == 1 and base_comp != "Sin comparación":
    st.caption("No se muestra variación: el año de referencia no tiene todos los meses del periodo.")
elif len(anios_sel) > 1:
    st.caption("Con varios años seleccionados los indicadores son acumulados; "
               "elige un solo año para ver la variación frente a la referencia.")

st.write("")

# ==================================================
# 8. PESTAÑAS
# ==================================================

(tab_res, tab_tend, tab_est, tab_proc, tab_oferta,
 tab_comp, tab_datos, tab_cal) = st.tabs(
    ["📊 Resumen", "📈 Tendencias", "🌤️ Estacionalidad", "🌎 Procedencia",
     "🏨 Oferta y ocupación", "⚖️ Comparador", "📋 Datos", "🔍 Calidad"]
)

# ---------------- RESUMEN ----------------
with tab_res:
    def medidor(valor, titulo, rango, meta=None, sufijo="", color=CELESTE):
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=0 if pd.isna(valor) else float(valor),
            number=dict(suffix=sufijo, font=dict(size=34, color=NAVY)),
            title=dict(text=titulo, font=dict(size=15, color=GRIS)),
            gauge=dict(
                axis=dict(range=rango),
                bar=dict(color=color),
                bgcolor="#EEF2F8",
                threshold=dict(line=dict(color=ROJO, width=4), thickness=0.8, value=meta)
                if meta is not None else None,
            ),
        ))
        fig.update_layout(height=230, margin=dict(l=20, r=20, t=50, b=10),
                          paper_bgcolor="rgba(0,0,0,0)")
        return fig

    g1, g2, g3 = st.columns(3)
    with g1:
        grafico(medidor(tnoh, "Ocupación de habitaciones", [0, 100], meta_tnoh, "%", MORADO))
        st.caption("✅ Meta alcanzada" if tnoh >= meta_tnoh
                   else f"⚠️ Faltan {meta_tnoh - tnoh:.1f} puntos para la meta")
    with g2:
        grafico(medidor(estancia, "Estancia promedio (noches)", [0, 3], meta_estancia, "", NARANJA))
        if estancia is not None:
            st.caption("✅ Meta alcanzada" if estancia >= meta_estancia
                       else f"⚠️ Faltan {meta_estancia - estancia:.2f} noches para la meta")
    with g3:
        grafico(medidor(pct_ext, "Turismo extranjero", [0, 100], None, "%", VERDE))
        st.caption("Porcentaje de arribos de visitantes extranjeros")

    st.divider()
    c_izq, c_der = st.columns([2, 1])

    with c_izq:
        etiqueta = metrica.title()
        fig = go.Figure()
        x = serie_filtrada["FECHA"]
        y = serie_filtrada[metrica]
        if tipo_grafico == "Barras":
            fig.add_trace(go.Bar(x=x, y=y, name=etiqueta, marker_color=CELESTE))
        elif tipo_grafico == "Área":
            fig.add_trace(go.Scatter(x=x, y=y, name=etiqueta, mode="lines",
                                     line=dict(color=CELESTE, width=3),
                                     fill="tozeroy", fillcolor="rgba(29,78,137,.15)"))
        else:
            fig.add_trace(go.Scatter(x=x, y=y, name=etiqueta, mode="lines+markers",
                                     line=dict(color=CELESTE, width=3)))
        if media_movil and len(serie_filtrada) >= 3:
            fig.add_trace(go.Scatter(
                x=x, y=y.rolling(3).mean(), name="Media móvil (3 meses)",
                mode="lines", line=dict(color=NARANJA, width=3, dash="dash"),
            ))
        fig.update_layout(title=f"Evolución mensual de {etiqueta.lower()}",
                          hovermode="x unified")
        fig.update_xaxes(rangeslider_visible=True)
        grafico(estilo(fig, 470))

    with c_der:
        por_anio = (
            serie_filtrada.groupby("ANIO", as_index=False)[metrica].sum()
        )
        por_anio["ANIO"] = por_anio["ANIO"].astype(str)
        fig = px.bar(por_anio, x="ANIO", y=metrica, text_auto=".3s",
                     title=f"{metrica.title()} por año")
        fig.update_traces(marker_color=VERDE, textposition="outside")
        fig.update_layout(xaxis_title=None, yaxis_title=None)
        grafico(estilo(fig, 470))

    st.subheader("Lectura rápida")
    mes_max = serie_filtrada.loc[serie_filtrada[metrica].idxmax()]
    mes_min = serie_filtrada.loc[serie_filtrada[metrica].idxmin()]
    insight(
        f"El mes más alto en **{metrica.lower()}** fue **{MESES[int(mes_max['MES'])]} "
        f"{int(mes_max['ANIO'])}** ({mes_max[metrica]:,.0f})."
    )
    insight(
        f"El mes más bajo fue **{MESES[int(mes_min['MES'])]} {int(mes_min['ANIO'])}** "
        f"({mes_min[metrica]:,.0f})."
    )
    if 2019 in serie_base["ANIO"].values and 2020 in serie_base["ANIO"].values:
        a19 = serie_base.loc[serie_base["ANIO"] == 2019, metrica].sum()
        a20 = serie_base.loc[serie_base["ANIO"] == 2020, metrica].sum()
        if a19:
            insight(
                f"Durante la pandemia (2020) los **{metrica.lower()}** cayeron "
                f"**{(1 - a20 / a19) * 100:.1f}%** frente a 2019."
            )

# ---------------- TENDENCIAS ----------------
with tab_tend:
    anual = (
        serie_filtrada.groupby("ANIO", as_index=False)[["ARRIBOS", "PERNOCTACIONES"]].sum()
        .sort_values("ANIO")
    )
    anual["VAR_ARRIBOS_%"] = anual["ARRIBOS"].pct_change(fill_method=None) * 100
    anual["VAR_PERNOCT_%"] = anual["PERNOCTACIONES"].pct_change(fill_method=None) * 100

    t1, t2 = st.columns(2)
    with t1:
        fig = px.bar(
            anual.dropna(subset=["VAR_ARRIBOS_%"]),
            x="ANIO", y="VAR_ARRIBOS_%", text_auto=".1f",
            title="Variación anual de arribos (%)",
        )
        fig.update_traces(
            marker_color=[
                VERDE if v >= 0 else ROJO
                for v in anual.dropna(subset=["VAR_ARRIBOS_%"])["VAR_ARRIBOS_%"]
            ],
            textposition="outside",
        )
        fig.update_layout(xaxis_title=None, yaxis_title="%")
        fig.update_xaxes(dtick=1)
        grafico(estilo(fig))
    with t2:
        base19 = serie_base[(serie_base["ANIO"] == 2019) & serie_base["MES"].isin(meses_sel)]
        if not base19.empty and base19["MES"].nunique() == len(meses_sel):
            ref = base19[metrica].sum()
            rec = anual[["ANIO", metrica]].copy()
            rec["INDICE"] = rec[metrica] / ref * 100
            fig = px.line(rec, x="ANIO", y="INDICE", markers=True,
                          title="Recuperación frente a 2019 (2019 = 100)")
            fig.add_hline(y=100, line_dash="dash", line_color=GRIS)
            fig.update_traces(line=dict(color=CELESTE, width=3))
            fig.update_xaxes(dtick=1)
            fig.update_layout(xaxis_title=None, yaxis_title="Índice")
            grafico(estilo(fig))
        else:
            st.info("El índice vs 2019 necesita 2019 con los mismos meses seleccionados.")

    if (anual["ANIO"] == 2025).any():
        st.warning(
            "2025 es parcial (enero-junio). Para compararlo con otros años usa "
            "el rango de meses 'Ene–Jun'."
        )

    st.subheader("Tabla anual")
    tabla = anual.rename(columns={
        "ANIO": "Año", "ARRIBOS": "Arribos", "PERNOCTACIONES": "Pernoctaciones",
        "VAR_ARRIBOS_%": "Var. arribos (%)", "VAR_PERNOCT_%": "Var. pernoct. (%)",
    })
    st.dataframe(
        tabla, width="stretch", hide_index=True,
        column_config={
            "Arribos": st.column_config.NumberColumn(format="%d"),
            "Pernoctaciones": st.column_config.NumberColumn(format="%d"),
            "Var. arribos (%)": st.column_config.NumberColumn(format="%.1f"),
            "Var. pernoct. (%)": st.column_config.NumberColumn(format="%.1f"),
        },
    )

# ---------------- ESTACIONALIDAD ----------------
with tab_est:
    est = serie_base[serie_base["ANIO"].isin(anios_sel)].copy()
    e1, e2 = st.columns(2)
    with e1:
        mapa = est.pivot(index="ANIO", columns="MES", values=metrica)
        mapa = mapa.reindex(columns=list(MESES.keys()))
        fig = px.imshow(
            mapa, aspect="auto", color_continuous_scale="Blues",
            labels=dict(x="Mes", y="Año", color=metrica.title()),
            title=f"Mapa de calor de {metrica.lower()}",
        )
        fig.update_xaxes(tickvals=list(MESES.keys()), ticktext=list(MESES_CORTO.values()))
        fig.update_yaxes(dtick=1)
        grafico(estilo(fig, 440))
    with e2:
        est["ANIO_S"] = est["ANIO"].astype(str)
        fig = px.line(
            est.sort_values("MES"), x="MES", y=metrica, color="ANIO_S", markers=True,
            title="Comparación mensual por año",
            labels={"MES": "Mes", "ANIO_S": "Año"},
        )
        fig.update_xaxes(tickvals=list(MESES.keys()), ticktext=list(MESES_CORTO.values()))
        fig.update_layout(hovermode="x unified", yaxis_title=None)
        grafico(estilo(fig, 440))

    normal = est[est["ANIO"].isin([a for a in est["ANIO"].unique() if a not in (2020, 2021, 2025)])]
    if not normal.empty:
        prom = normal.groupby("MES")[metrica].mean()
        if prom.notna().any():
            insight(
                f"Sin contar 2020, 2021 (pandemia) ni 2025 (parcial), el mes de mayor "
                f"{metrica.lower()} es **{MESES[int(prom.idxmax())]}** y el de menor es "
                f"**{MESES[int(prom.idxmin())]}**."
            )

# ---------------- PROCEDENCIA ----------------
with tab_proc:
    if nac is None or ext is None:
        st.info("La base no tiene columnas de procedencia.")
    else:
        p1, p2 = st.columns([1, 2])
        with p1:
            fig = px.pie(
                pd.DataFrame({"Procedencia": ["Nacionales", "Extranjeros"],
                              "Arribos": [nac, ext]}),
                names="Procedencia", values="Arribos", hole=0.55,
                title="Participación por procedencia",
                color_discrete_sequence=[CELESTE, NARANJA],
            )
            fig.update_traces(textinfo="percent+label")
            fig.update_layout(showlegend=False)
            grafico(estilo(fig, 430))
        with p2:
            origen = (
                serie_filtrada.groupby("ANIO", as_index=False)[["ARRIBOS_NAC", "ARRIBOS_EXT"]].sum()
            )
            origen["ANIO"] = origen["ANIO"].astype(str)
            largo = origen.melt("ANIO", var_name="Procedencia", value_name="Arribos")
            largo["Procedencia"] = largo["Procedencia"].map(
                {"ARRIBOS_NAC": "Nacionales", "ARRIBOS_EXT": "Extranjeros"}
            )
            fig = px.bar(
                largo, x="ANIO", y="Arribos", color="Procedencia", barmode="stack",
                title="Arribos por año según procedencia",
                color_discrete_map={"Nacionales": CELESTE, "Extranjeros": NARANJA},
            )
            fig.update_layout(xaxis_title=None, yaxis_title=None)
            grafico(estilo(fig, 430))

        origen["% extranjeros"] = origen["ARRIBOS_EXT"] / (
            origen["ARRIBOS_NAC"] + origen["ARRIBOS_EXT"]
        ) * 100
        fig = px.line(origen, x="ANIO", y="% extranjeros", markers=True,
                      title="Peso del turismo extranjero (% de arribos)")
        fig.update_traces(line=dict(color=NARANJA, width=3))
        fig.update_layout(xaxis_title=None, yaxis_title="%")
        grafico(estilo(fig, 330))

# ---------------- OFERTA Y OCUPACION ----------------
with tab_oferta:
    o1, o2 = st.columns(2)
    periodo = df[df["ANIO"].isin(anios_sel) & df["MES"].isin(meses_sel)]

    with o1:
        # Una sola capa: tipo especifico + categoria "TODAS"
        por_tipo = (
            periodo[(periodo["CLASE_N"] != "TODAS") & (periodo["CATEGORIA_N"] == "TODAS")]
            .groupby("CLASE_N", as_index=False)[metrica].sum()
        )
        por_tipo = por_tipo[por_tipo[metrica] > 0]
        fig = px.bar(
            por_tipo.sort_values(metrica), x=metrica, y="CLASE_N", orientation="h",
            text_auto=".3s", title=f"{metrica.title()} por tipo de alojamiento",
        )
        fig.update_traces(marker_color=CELESTE)
        fig.update_layout(xaxis_title=None, yaxis_title=None)
        grafico(estilo(fig, 400))

    with o2:
        # Una sola capa: categoria (estrellas) con clase "TODAS"
        por_cat = (
            periodo[(periodo["CLASE_N"] == "TODAS") & (periodo["CATEGORIA_N"] != "TODAS")]
            .groupby("CATEGORIA_N", as_index=False)[metrica].sum()
        )
        por_cat = por_cat[por_cat[metrica] > 0]
        fig = px.pie(por_cat, names="CATEGORIA_N", values=metrica, hole=0.5,
                     title=f"{metrica.title()} por categoría")
        fig.update_traces(textinfo="percent+label")
        fig.update_layout(showlegend=False)
        grafico(estilo(fig, 400))

    o3, o4 = st.columns(2)
    with o3:
        fig = px.line(
            serie_filtrada, x="FECHA", y="TNOH", markers=True,
            title="Tasa neta de ocupación de habitaciones (%)",
        )
        fig.update_traces(line=dict(color=MORADO, width=3))
        fig.update_layout(xaxis_title=None, yaxis_title="%")
        grafico(estilo(fig, 380))
    with o4:
        oferta = serie_filtrada.groupby("ANIO", as_index=False).agg(
            Establecimientos=("ESTABLECIMIENTOS", "mean"),
            Habitaciones=("HABITACIONES", "mean"),
        )
        oferta["ANIO"] = oferta["ANIO"].astype(str)
        fig = px.bar(oferta, x="ANIO", y="Habitaciones", text_auto=".0f",
                     title="Habitaciones disponibles (promedio mensual)")
        fig.update_traces(marker_color=VERDE)
        fig.update_layout(xaxis_title=None, yaxis_title=None)
        grafico(estilo(fig, 380))

# ---------------- COMPARADOR ----------------
with tab_comp:
    st.subheader("⚖️ Comparar dos años")
    st.caption("Usa el segmento y el rango de meses del panel lateral.")
    cA, cB = st.columns(2)
    anio_a = cA.selectbox("Año A", anios_disp, index=max(len(anios_disp) - 3, 0))
    anio_b = cB.selectbox("Año B", anios_disp, index=max(len(anios_disp) - 2, 0))

    def resumen_anio(anio):
        d = serie_base[(serie_base["ANIO"] == anio) & serie_base["MES"].isin(meses_sel)]
        return d

    da, db = resumen_anio(anio_a), resumen_anio(anio_b)
    if da.empty or db.empty:
        st.info("Uno de los años no tiene datos para los meses elegidos.")
    else:
        if set(da["MES"]) != set(db["MES"]):
            st.warning("Los años no tienen los mismos meses con datos; la comparación puede no ser equivalente.")

        def indicadores(d):
            arr, per = d["ARRIBOS"].sum(), d["PERNOCTACIONES"].sum()
            return {
                "Arribos": arr,
                "Pernoctaciones": per,
                "Estancia (noches)": per / arr if arr else float("nan"),
                "Ocupación hab. (%)": d["TNOH"].mean(),
                "Arribos extranjeros": d["ARRIBOS_EXT"].sum(),
                "Empleo (promedio)": d["EMPLEO"].mean(),
            }

        ia, ib = indicadores(da), indicadores(db)
        tabla = pd.DataFrame({
            "Indicador": list(ia.keys()),
            f"{anio_a}": list(ia.values()),
            f"{anio_b}": list(ib.values()),
        })
        tabla["Variación B vs A (%)"] = (tabla[f"{anio_b}"] / tabla[f"{anio_a}"] - 1) * 100
        st.dataframe(
            tabla, width="stretch", hide_index=True,
            column_config={
                f"{anio_a}": st.column_config.NumberColumn(format="%.2f"),
                f"{anio_b}": st.column_config.NumberColumn(format="%.2f"),
                "Variación B vs A (%)": st.column_config.NumberColumn(format="%.1f"),
            },
        )

        mensual_comp = pd.concat([
            da.assign(AÑO=str(anio_a)), db.assign(AÑO=str(anio_b))
        ])
        fig = px.bar(
            mensual_comp.sort_values("MES"), x="NOMBRE_MES", y=metrica, color="AÑO",
            barmode="group", title=f"{metrica.title()} mensual: {anio_a} vs {anio_b}",
            category_orders={"NOMBRE_MES": list(MESES.values())},
            color_discrete_sequence=[CELESTE, NARANJA],
        )
        fig.update_layout(xaxis_title=None, yaxis_title=None)
        grafico(estilo(fig, 420))

# ---------------- DATOS ----------------
with tab_datos:
    st.subheader("Base filtrada")
    st.caption("Una fila por mes, según el tipo y la categoría elegidos.")

    columnas = [
        "ANIO", "NOMBRE_MES", "CLASE_N", "CATEGORIA_N", "ESTABLECIMIENTOS",
        "HABITACIONES", "PLAZAS_CAMA", "TNOH", "TNOC", "ARRIBOS", "ARRIBOS_NAC",
        "ARRIBOS_EXT", "PERNOCTACIONES", "EMPLEO",
    ]
    columnas = [c for c in columnas if c in serie_filtrada.columns]
    mostrar = st.multiselect("Columnas a mostrar", columnas, default=columnas)
    vista = serie_filtrada[mostrar] if mostrar else serie_filtrada[columnas]

    st.dataframe(vista, width="stretch", hide_index=True)

    d1, d2, _ = st.columns([1, 1, 3])
    d1.download_button(
        "📥 Descargar CSV",
        vista.to_csv(index=False).encode("utf-8-sig"),
        file_name="hoteles_puno_filtrado.csv",
        mime="text/csv",
    )
    try:
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as escritor:
            vista.to_excel(escritor, index=False, sheet_name="Datos")
        d2.download_button(
            "📥 Descargar Excel",
            buffer.getvalue(),
            file_name="hoteles_puno_filtrado.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except ImportError:
        d2.caption("Instala openpyxl para exportar a Excel.")

# ---------------- CALIDAD ----------------
with tab_cal:
    st.subheader("Control de calidad")
    q1, q2, q3 = st.columns(3)
    q1.metric("Registros en la base", f"{len(df):,}")
    q2.metric("Años", f"{df['ANIO'].min()}–{df['ANIO'].max()}")
    q3.metric("Meses en la selección", f"{len(serie_filtrada):,}")

    st.info(
        "La base mezcla niveles de agregación (total, tipo y categoría). "
        "El dashboard usa solo UNA fila por mes según el filtro elegido, "
        "para no duplicar cifras. Los códigos de 2019-2023 (01, 03, 05, TT...) "
        "se unificaron con los nombres de 2024-2025 (Hotel, Hostal, Albergue, "
        "Todas consolidadas). Conviene confirmar esa equivalencia con el "
        "diccionario de MINCETUR."
    )

    st.markdown("**Valores faltantes (solo columnas usadas)**")
    usadas = [c for c in columnas if c in df.columns]
    faltantes = df[usadas].isna().sum().rename("Faltantes").to_frame()
    st.dataframe(faltantes, width="stretch")

    st.markdown("**Registros por año**")
    reg = df.groupby("ANIO").size().rename("Registros").to_frame()
    st.dataframe(reg, width="stretch")

# ==================================================
# 9. PIE DE PAGINA
# ==================================================

st.divider()
st.caption(
    "Business Analytics · Hoteles Puno | Universidad Nacional del Altiplano | "
    "Periodo 2019-2025 | Fuente declarada: MINCETUR"
)
