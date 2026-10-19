import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from core.engine import generate_run, summarize_run
from data.database import init_db, save_run, list_runs

st.set_page_config(page_title="MENFA PIG MFL", page_icon="🛢️", layout="wide")
init_db()

st.markdown("""
<style>
.stApp { background: #f5f5f7; }
section[data-testid="stSidebar"] { background: #24232d; }
section[data-testid="stSidebar"] * { color: #ffffff; }
.menfa-title { color: #5b2a86; font-weight: 800; letter-spacing: .5px; }
.metric-card { background: white; padding: 14px; border-radius: 12px; border-left: 5px solid #e87524; }
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("## 🟠 MENFA")
st.sidebar.caption("ECOSISTEMA DE CAPACITACIÓN Y TECNOLOGÍA")
page = st.sidebar.radio("Navegación", ["Centro de control", "Análisis MFL", "Informe de corrida", "Historial"])

st.markdown('<h1 class="menfa-title">MENFA PIG MFL</h1>', unsafe_allow_html=True)
st.caption("Simulador avanzado de inspección interna de gasoductos · Versión educativa 0.1.0")

if "run_data" not in st.session_state:
    st.session_state.run_data = None
if "run_config" not in st.session_state:
    st.session_state.run_config = None

if page == "Centro de control":
    st.subheader("Configuración de misión")
    with st.form("run_config"):
        a, b, c = st.columns(3)
        with a:
            duct_id = st.text_input("Identificación del gasoducto", "GAS-MENFA-001")
            length_km = st.slider("Longitud del tramo (km)", 1, 50, 12)
            diameter_mm = st.selectbox("Diámetro nominal (mm)", [300, 400, 500, 600, 750, 900, 1050, 1200], index=4)
        with b:
            wall_mm = st.slider("Espesor nominal (mm)", 5.0, 20.0, 10.0, 0.5)
            speed_m_s = st.slider("Velocidad promedio del PIG (m/s)", 0.5, 5.0, 2.0, 0.1)
            channels = st.selectbox("Canales MFL simulados", [8, 16, 32, 48], index=2)
        with c:
            noise = st.select_slider("Ruido de señal", options=["Bajo", "Medio", "Alto"], value="Medio")
            scenario = st.selectbox("Escenario", [
                "A — Corrosión localizada",
                "B — Corrosión agrupada",
                "C — Calidad de datos degradada",
                "D — Corrida integral"
            ])
            seed = st.number_input("Semilla reproducible", min_value=1, max_value=999999, value=20261017)
        submitted = st.form_submit_button("▶ Ejecutar corrida simulada", type="primary", use_container_width=True)

    if submitted:
        config = {
            "duct_id": duct_id.strip() or "GAS-MENFA-001",
            "length_km": length_km,
            "diameter_mm": diameter_mm,
            "wall_mm": wall_mm,
            "speed_m_s": speed_m_s,
            "channels": channels,
            "noise": noise,
            "scenario": scenario,
            "seed": int(seed)
        }
        with st.spinner("Generando recorrido, señales y eventos sintéticos..."):
            st.session_state.run_data = generate_run(config)
            st.session_state.run_config = config
            save_run(config, summarize_run(st.session_state.run_data))
        st.success("Corrida simulada finalizada. Los resultados son sintéticos y reproducibles.")

    if st.session_state.run_data is not None:
        data = st.session_state.run_data
        config = st.session_state.run_config
        summary = summarize_run(data)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Longitud inspeccionada", f"{config['length_km']:.1f} km")
        m2.metric("Velocidad promedio", f"{config['speed_m_s']:.1f} m/s")
        m3.metric("Candidatos detectados", summary["detected_count"])
        m4.metric("Canales simulados", config["channels"])
        st.subheader("Resumen del recorrido")
        route = pd.DataFrame({"Distancia (km)": data["distance_km"], "Velocidad (m/s)": data["speed_m_s_series"]})
        fig = px.line(route, x="Distancia (km)", y="Velocidad (m/s)", title="Velocidad simulada a lo largo del gasoducto")
        fig.update_layout(height=330, margin=dict(l=20,r=20,t=55,b=20))
        st.plotly_chart(fig, use_container_width=True)
        st.info("Esta primera versión ejecuta una corrida completa de forma instantánea. La animación y los controles paso a paso quedan previstos para una siguiente iteración.")
    else:
        st.info("Configure la misión y ejecute una corrida para generar señales MFL, indicaciones y un informe.")

elif page == "Análisis MFL":
    if st.session_state.run_data is None:
        st.warning("Primero ejecute una corrida desde Centro de control.")
    else:
        data = st.session_state.run_data
        st.subheader("Monitor de señales MFL")
        channel = st.selectbox("Canal circunferencial", list(range(data["channels"].shape[0])), format_func=lambda x: f"Canal {x+1}")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=data["distance_km"], y=data["channels"][channel], mode="lines", name=f"Canal {channel+1}"))
        fig.update_layout(title="Señal sintética frente a distancia", xaxis_title="Distancia (km)", yaxis_title="Amplitud relativa (u.a.)", height=420)
        st.plotly_chart(fig, use_container_width=True)
        st.subheader("Mapa de calor multicanal")
        heat = go.Figure(data=go.Heatmap(z=data["channels"], x=data["distance_km"], y=[f"C{i+1}" for i in range(data["channels"].shape[0])], colorscale="Plasma"))
        heat.update_layout(xaxis_title="Distancia (km)", yaxis_title="Canal", height=440)
        st.plotly_chart(heat, use_container_width=True)
        st.caption("Las amplitudes y defectos son sintéticos para entrenamiento; no representan una calibración real ni una medición certificada.")

elif page == "Informe de corrida":
    if st.session_state.run_data is None:
        st.warning("Primero ejecute una corrida desde Centro de control.")
    else:
        data = st.session_state.run_data
        config = st.session_state.run_config
        detections = pd.DataFrame(data["detections"])
        summary = summarize_run(data)
        st.subheader("Informe preliminar de inspección")
        st.write(f"**Ducto:** {config['duct_id']}  ")
        st.write(f"**Escenario:** {config['scenario']}  ")
        st.write(f"**Longitud:** {config['length_km']} km · **Diámetro:** {config['diameter_mm']} mm · **Espesor nominal:** {config['wall_mm']} mm")
        st.warning("Informe educativo generado a partir de datos sintéticos. No utilizar para decisiones reales de integridad.")
        st.metric("Indicaciones candidatas", summary["detected_count"])
        if len(detections):
            st.dataframe(detections, use_container_width=True, hide_index=True)
            st.download_button("Descargar indicaciones CSV", detections.to_csv(index=False).encode("utf-8"), file_name="menfa_pig_mfl_indicaciones.csv", mime="text/csv")
        else:
            st.write("No se generaron candidatos en esta corrida.")
        report_text = (
            "MENFA PIG MFL — INFORME EDUCATIVO\n"
            f"Ducto: {config['duct_id']}\nEscenario: {config['scenario']}\n"
            f"Longitud: {config['length_km']} km\nDiámetro: {config['diameter_mm']} mm\n"
            f"Espesor nominal: {config['wall_mm']} mm\n"
            f"Indicaciones candidatas: {summary['detected_count']}\n\n"
            "ADVERTENCIA: datos sintéticos. Este informe no es apto para evaluación de integridad real."
        )
        st.download_button("Descargar resumen TXT", report_text.encode("utf-8"), file_name="menfa_pig_mfl_informe.txt", mime="text/plain")

else:
    st.subheader("Historial local de corridas")
    history = list_runs()
    if history.empty:
        st.info("Todavía no hay corridas guardadas en esta instalación.")
    else:
        st.dataframe(history, use_container_width=True, hide_index=True)
        st.download_button("Exportar historial CSV", history.to_csv(index=False).encode("utf-8"), file_name="menfa_pig_mfl_historial.csv", mime="text/csv")
