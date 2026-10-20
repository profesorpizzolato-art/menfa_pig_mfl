from __future__ import annotations

import sys
from pathlib import Path

# Añade la ruta base y la carpeta del módulo explícitamente al path de Python
ROOT_DIR = Path(__file__).resolve().parent
SUB_DIR = ROOT_DIR / "menfa_pig_mfl_v0_2"

for p in [str(ROOT_DIR), str(SUB_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import json
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Importación directa e independiente de la estructura de contenedores remotos
try:
    from core.engine import simulate_mfl, detect_indications, build_pipe_figure
    from data.database import DEFAULT_DB, initialize, save_run, list_runs
except ModuleNotFoundError:
    try:
        from menfa_pig_mfl_v0_2.core.engine import simulate_mfl, detect_indications, build_pipe_figure
        from menfa_pig_mfl_v0_2.data.database import DEFAULT_DB, initialize, save_run, list_runs
    except ModuleNotFoundError:
        # Última alternativa buscando de manera relativa interna
        from .core.engine import simulate_mfl, detect_indications, build_pipe_figure
        from .data.database import DEFAULT_DB, initialize, save_run, list_runs

st.set_page_config(page_title="MENFA PIG MFL · Suite avanzada", page_icon="🛢️", layout="wide")

MENFA_CSS = """
<style>
:root { --menfa-orange: #f97316; --menfa-violet: #5b21b6; }
[data-testid="stAppViewContainer"] { background: linear-gradient(180deg, rgba(91,33,182,.035), transparent 250px); }
[data-testid="stSidebar"] { border-right: 2px solid #5b21b6; }
.menfa-header { padding: 1.1rem 1.3rem; border-radius: 14px; color: white; background: linear-gradient(110deg,#25232b,#5b21b6 70%,#f97316); margin-bottom: 1rem; }
.menfa-sub { color: #e9e3f5; margin-bottom: 0; }
</style>
"""
st.markdown(MENFA_CSS, unsafe_allow_html=True)
st.markdown('<div class="menfa-header"><h1>🛢️ MENFA PIG MFL</h1><p class="menfa-sub">Suite avanzada · Gemelo digital educativo · Modelo híbrido MFL · v0.2</p></div>', unsafe_allow_html=True)
st.warning("ENTORNO EDUCATIVO: las señales, defectos y métricas son sintéticos. No utilizar para decisiones de integridad, operación o reparación de un gasoducto real.")

initialize(DEFAULT_DB)
if "run_data" not in st.session_state:
    st.session_state.run_data = None
if "pig_position" not in st.session_state:
    st.session_state.pig_position = 0.0

page = st.sidebar.radio("Módulos", ["Centro de control 3D", "Laboratorio MFL", "Informe de corrida", "Historial", "Acerca del modelo"])
st.sidebar.markdown("---")
st.sidebar.caption("MENFA Capacitaciones · Simulación educativa")


def current_run():
    return st.session_state.run_data

if page == "Centro de control 3D":
    st.subheader("Centro de control operacional")
    with st.sidebar.expander("Parámetros de la corrida", expanded=True):
        operator = st.text_input("Operador / alumno", "Operador MENFA")
        scenario = st.selectbox("Escenario", ["A · Corrida nominal", "B · Ruido elevado", "C · Canal degradado", "D · Odómetro con desviación"])
        length_m = st.slider("Longitud del tramo (m)", 200, 5000, 1200, 100)
        speed = st.slider("Velocidad simulada (m/s)", 0.2, 4.0, 1.2, 0.1)
        channels = st.select_slider("Canales MFL", options=[4, 8, 12, 16], value=8)
        defect_count = st.slider("Anomalías de referencia", 0, 25, 8)
        seed = st.number_input("Semilla reproducible", min_value=1, max_value=999999, value=2026, step=1)
        noise = st.slider("Nivel de ruido", 0.0, 0.5, 0.08, 0.01)
        sensitivity = st.slider("Sensibilidad sintética", 0.3, 2.0, 1.0, 0.1)
        threshold = st.slider("Umbral de detección", 0.05, 1.5, 0.35, 0.05)
        failed_channel = None
        if scenario.startswith("B"):
            noise = min(0.5, noise * 2.2)
        elif scenario.startswith("C"):
            failed_channel = min(2, channels - 1)
        elif scenario.startswith("D"):
            st.caption("El odómetro se mostrará con una desviación educativa del +2%.")
        run_btn = st.button("▶ Generar / ejecutar corrida", type="primary", use_container_width=True)
    if run_btn:
        frame, defects, metadata = simulate_mfl(length_m=length_m, sample_count=2400, channels=channels,
            seed=int(seed), noise=noise, sensitivity=sensitivity, defect_count=defect_count,
            failed_channel=failed_channel, speed_m_s=speed)
        indications = detect_indications(frame, threshold=threshold)
        if scenario.startswith("D"):
            frame["odometer_m"] = frame["distance_m"] * 1.02
        else:
            frame["odometer_m"] = frame["distance_m"]
        st.session_state.run_data = {"frame": frame, "defects": defects, "metadata": metadata,
            "indications": indications, "threshold": threshold, "operator": operator,
            "scenario": scenario, "length_m": length_m, "speed_m_s": speed, "channels": channels,
            "seed": int(seed), "saved_id": None}
        st.session_state.pig_position = 0.0
    run = current_run()
    if run:
        frame, defects = run["frame"], run["defects"]
        cols = st.columns(4)
        cols[0].metric("Recorrido", f"{run['length_m']:,.0f} m")
        cols[1].metric("Duración simulada", f"{run['length_m']/run['speed_m_s']/60:.1f} min")
        cols[2].metric("Canales", str(run["channels"]))
        cols[3].metric("Indicaciones", str(len(run["indications"])))
        pos = st.slider("Posición del PIG (m)", 0.0, float(run["length_m"]), float(st.session_state.pig_position), max(1.0, run["length_m"]/200), key="pig_pos_slider")
        st.session_state.pig_position = pos
        st.plotly_chart(build_pipe_figure(run["length_m"], pos, defects), use_container_width=True, config={"displaylogo": False})
        st.caption("Vista 3D esquemática; no representa geometría de ingeniería ni escala dimensional validada.")
        a, b = st.columns(2)
        with a:
            if st.button("💾 Guardar corrida en historial", type="primary"):
                if run["saved_id"] is None:
                    run_id = save_run({"operator": run["operator"], "scenario": run["scenario"], "seed": run["seed"],
                        "length_m": run["length_m"], "speed_m_s": run["speed_m_s"], "channels": run["channels"],
                        "reference_defects": len(run["defects"]), "detected_indications": len(run["indications"]),
                        "threshold": run["threshold"], "metadata": run["metadata"]})
                    run["saved_id"] = run_id
                    st.success(f"Corrida guardada con ID {run_id}.")
                else:
                    st.info(f"Esta corrida ya está guardada con ID {run['saved_id']}.")
        with b:
            st.download_button("Descargar datos CSV", frame.to_csv(index=False).encode("utf-8"),
                file_name=f"menfa_pig_mfl_seed_{run['seed']}.csv", mime="text/csv")
    else:
        st.info("Configurá la corrida en el panel lateral y seleccioná **Generar / ejecutar corrida** para crear el gemelo digital y las señales.")

elif page == "Laboratorio MFL":
    st.subheader("Laboratorio de instrumentación y análisis MFL")
    run = current_run()
    if not run:
        st.info("Primero generá una corrida desde Centro de control 3D.")
    else:
        frame = run["frame"]
        channel_cols = run["metadata"]["channel_columns"]
        chosen = st.multiselect("Canales para visualizar", channel_cols, default=channel_cols[:min(4, len(channel_cols))])
        max_points = st.slider("Muestras a mostrar", 200, min(2400, len(frame)), min(1200, len(frame)), 100)
        subset = frame.iloc[::max(1, len(frame)//max_points)]
        fig = go.Figure()
        for col in chosen:
            fig.add_trace(go.Scatter(x=subset["distance_m"], y=subset[col], mode="lines", name=col))
        fig.update_layout(height=420, xaxis_title="Distancia (m)", yaxis_title="Amplitud sintética (u.a.)", hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True)
        heat_cols = chosen or channel_cols
        heat = frame[heat_cols].iloc[::max(1, len(frame)//600)].T
        heat_fig = go.Figure(go.Heatmap(z=heat.values, x=frame["distance_m"].iloc[::max(1, len(frame)//600)], y=heat_cols, colorscale="RdBu", zmid=0))
        heat_fig.update_layout(height=300, xaxis_title="Distancia (m)", yaxis_title="Canal")
        st.markdown("#### Mapa de amplitud multicanal")
        st.plotly_chart(heat_fig, use_container_width=True)
        st.markdown("#### Indicaciones detectadas por umbral")
        st.caption(f"Umbral aplicado: {run['threshold']:.2f} u.a. · La detección es una regla didáctica, no un algoritmo de calificación industrial.")
        st.dataframe(run["indications"].round(3), use_container_width=True, hide_index=True)
        st.markdown("#### Anomalías de referencia (verdad de terreno sintética)")
        st.dataframe(pd.DataFrame([d.as_dict() for d in run["defects"]]), use_container_width=True, hide_index=True)

elif page == "Informe de corrida":
    st.subheader("Informe técnico educativo")
    run = current_run()
    if not run:
        st.info("No hay una corrida activa. Generá una desde Centro de control 3D.")
    else:
        detected = run["indications"]
        defects = run["defects"]
        meta = run["metadata"]
        report = {
            "marca": "MENFA Capacitaciones", "producto": "MENFA PIG MFL Suite avanzada v0.2",
            "clasificacion": "SIMULACIÓN EDUCATIVA — DATOS SINTÉTICOS",
            "operador": run["operator"], "escenario": run["scenario"], "semilla": run["seed"],
            "longitud_m": run["length_m"], "velocidad_m_s": run["speed_m_s"],
            "duracion_simulada_s": round(run["length_m"] / run["speed_m_s"], 2),
            "canales": run["channels"], "anomalías_referencia": len(defects),
            "indicaciones_detectadas": len(detected), "umbral": run["threshold"],
            "modelo": meta["model"],
            "limitacion": "No apto para evaluación de integridad, reparación u operación de gasoductos reales."
        }
        st.json(report, expanded=True)
        st.download_button("Descargar informe JSON", json.dumps(report, ensure_ascii=False, indent=2).encode("utf-8"),
                           file_name=f"MENFA_PIG_MFL_informe_{run['seed']}.json", mime="application/json")
        st.download_button("Descargar tabla de anomalías CSV", pd.DataFrame([d.as_dict() for d in defects]).to_csv(index=False).encode("utf-8"),
                           file_name=f"MENFA_PIG_MFL_anomalias_{run['seed']}.csv", mime="text/csv")
        st.info("El informe PDF y el módulo de evaluación de alumnos quedan definidos para una iteración posterior; esta versión entrega informe JSON y tablas CSV reproducibles.")

elif page == "Historial":
    st.subheader("Historial de corridas guardadas")
    runs = list_runs(DEFAULT_DB, limit=200)
    if not runs:
        st.info("Todavía no hay corridas guardadas. Generá una y usá el botón Guardar corrida en historial.")
    else:
        df = pd.DataFrame(runs)
        if "metadata_json" in df:
            df = df.drop(columns=["metadata_json"])
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.download_button("Exportar historial CSV", df.to_csv(index=False).encode("utf-8"), "MENFA_PIG_MFL_historial.csv", "text/csv")

else:
    st.subheader("Arquitectura y límites del modelo")
    st.markdown("""
**Enfoque híbrido:** modelo operacional simplificado + generación sintética de respuestas MFL + geometría 3D esquemática.

- `app.py`: interfaz Streamlit y estado de sesión.
- `core/engine.py`: escenarios, anomalías de referencia, señales multicanal, detección por umbral y vista 3D.
- `data/database.py`: persistencia SQLite de corridas.
- `tests/`: pruebas unitarias reproducibles.

**Incluido en v0.2:** 3D interactivo, escenarios nominal/ruido/canal degradado/odómetro desviado, señales multicanal, heatmap, umbral de indicaciones, verdad de terreno sintética, CSV/JSON e historial.

**No incluido aún:** solver electromagnético, dimensionamiento real de defectos, calibración contra herramienta comercial, certificación de integridad, sincronización física con hardware, cuentas multiusuario, PDF institucional y evaluación LMS.

**Seguridad de uso:** el software es exclusivamente didáctico. Las indicaciones y parámetros no son una recomendación para operar, reparar o aceptar un gasoducto real.
""")
