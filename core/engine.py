"""Deterministic educational hybrid MFL pipeline inspection model.

Signals are synthetic training data. This is not a validated electromagnetic
solver and must not be used to assess real pipeline fitness-for-service.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Defect:
    defect_id: str
    distance_m: float
    clock_position_deg: float
    length_mm: float
    width_mm: float
    depth_pct: float
    defect_type: str = "Metal loss"

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def generate_defects(length_m: float, seed: int = 17, count: int = 8) -> list[Defect]:
    """Create reproducible reference anomalies within a pipeline length."""
    if length_m <= 0:
        raise ValueError("length_m must be positive")
    if count < 0:
        raise ValueError("count cannot be negative")
    rng = np.random.default_rng(seed)
    types = ["Metal loss", "Pitting", "Axial groove", "Circumferential feature"]
    result = []
    for i in range(count):
        result.append(Defect(
            defect_id=f"REF-{i + 1:03d}",
            distance_m=round(float(rng.uniform(5, max(5.01, length_m - 5))) if length_m > 10 else float(length_m * (i + 1) / (count + 1)), 2),
            clock_position_deg=round(float(rng.uniform(0, 360)), 1),
            length_mm=round(float(rng.uniform(12, 180)), 1),
            width_mm=round(float(rng.uniform(4, 65)), 1),
            depth_pct=round(float(rng.uniform(8, 65)), 1),
            defect_type=types[i % len(types)],
        ))
    return sorted(result, key=lambda d: d.distance_m)


def simulate_mfl(length_m: float = 1000, sample_count: int = 2000, channels: int = 8,
                  seed: int = 17, noise: float = 0.08, sensitivity: float = 1.0,
                  defect_count: int = 8, failed_channel: int | None = None,
                  speed_m_s: float = 1.0) -> tuple[pd.DataFrame, list[Defect], dict[str, Any]]:
    """Generate a repeatable multichannel MFL-like dataset and reference defects."""
    if length_m <= 0:
        raise ValueError("length_m must be > 0")
    if sample_count < 20:
        raise ValueError("sample_count must be >= 20")
    if channels < 1:
        raise ValueError("channels must be >= 1")
    if noise < 0 or sensitivity <= 0 or speed_m_s <= 0:
        raise ValueError("noise must be >= 0; sensitivity and speed must be > 0")
    if failed_channel is not None and not 0 <= failed_channel < channels:
        raise ValueError("failed_channel index is outside available channels")

    rng = np.random.default_rng(seed)
    distance = np.linspace(0.0, length_m, sample_count)
    defects = generate_defects(length_m, seed=seed + 101, count=defect_count)
    data: dict[str, Any] = {
        "distance_m": distance,
        "time_s": distance / speed_m_s,
    }
    channel_cols = []
    for ch in range(channels):
        signal = rng.normal(0.0, noise, sample_count)
        signal += 0.025 * np.sin(distance / (12.0 + ch * 1.5))
        for defect in defects:
            # Simplified synthetic response: amplitude relates to depth and sensitivity.
            center = defect.distance_m
            sigma = max(0.7, defect.length_mm / 1000 * 1.8)
            amp = (defect.depth_pct / 65.0) * sensitivity * (0.65 + 0.35 * np.cos(np.deg2rad(defect.clock_position_deg - ch * 360 / channels)))
            x = (distance - center) / sigma
            bipolar = amp * (-x) * np.exp(-0.5 * x * x)
            signal += bipolar
        col = f"ch_{ch + 1:02d}"
        if failed_channel == ch:
            signal[:] = 0.0
        data[col] = signal
        channel_cols.append(col)
    frame = pd.DataFrame(data)
    frame["magnitude"] = frame[channel_cols].abs().max(axis=1)
    metadata = {
        "seed": int(seed), "length_m": float(length_m), "sample_count": int(sample_count),
        "channels": int(channels), "noise": float(noise), "sensitivity": float(sensitivity),
        "speed_m_s": float(speed_m_s), "failed_channel": failed_channel,
        "channel_columns": channel_cols,
        "run_duration_s": float(length_m / speed_m_s),
        "reference_defect_count": len(defects),
        "model": "Hybrid educational synthetic MFL",
    }
    return frame, defects, metadata


def detect_indications(frame: pd.DataFrame, threshold: float = 0.35,
                       min_separation_m: float = 3.0) -> pd.DataFrame:
    """Threshold the synthetic max-channel magnitude and merge nearby samples."""
    if "magnitude" not in frame or "distance_m" not in frame:
        raise ValueError("frame must contain distance_m and magnitude columns")
    if threshold < 0 or min_separation_m < 0:
        raise ValueError("threshold and min_separation_m must be non-negative")
    hits = frame.loc[frame["magnitude"] >= threshold, ["distance_m", "magnitude"]]
    if hits.empty:
        return pd.DataFrame(columns=["distance_m", "peak_magnitude", "sample_count"])
    groups = (hits["distance_m"].diff().fillna(np.inf) > min_separation_m).cumsum()
    rows = []
    for _, group in hits.groupby(groups):
        idx = group["magnitude"].idxmax()
        rows.append({"distance_m": float(frame.loc[idx, "distance_m"]),
                     "peak_magnitude": float(frame.loc[idx, "magnitude"]),
                     "sample_count": int(len(group))})
    return pd.DataFrame(rows).sort_values("distance_m").reset_index(drop=True)


def build_pipe_figure(length_m: float, pig_position_m: float, defects: list[Defect],
                      diameter_m: float = 0.8):
    """Return a Plotly 3D cutaway-style pipe view."""
    import plotly.graph_objects as go
    theta = np.linspace(0, 2 * np.pi, 36)
    x = np.linspace(0, length_m, 70)
    X, T = np.meshgrid(x, theta)
    radius = diameter_m / 2
    Y = radius * np.cos(T)
    Z = radius * np.sin(T)
    fig = go.Figure()
    fig.add_trace(go.Surface(x=X, y=Y, z=Z, opacity=0.20, showscale=False,
                             colorscale=[[0, "#7b8794"], [1, "#cbd5e1"]],
                             name="Pared del ducto", hoverinfo="skip"))
    # Longitudinal guide rails and reference welds.
    for ang in (0, np.pi / 2, np.pi, 3 * np.pi / 2):
        fig.add_trace(go.Scatter3d(x=x, y=np.full_like(x, radius*np.cos(ang)),
                                   z=np.full_like(x, radius*np.sin(ang)), mode="lines",
                                   line=dict(color="#64748b", width=3), showlegend=False,
                                   hoverinfo="skip"))
    for weld_x in np.arange(0, length_m + 0.1, max(50, length_m / 10)):
        fig.add_trace(go.Scatter3d(x=[weld_x, weld_x], y=[-radius, radius], z=[0, 0],
                                   mode="lines", line=dict(color="#f97316", width=3),
                                   name="Soldadura de referencia", showlegend=False,
                                   hovertemplate=f"Soldadura · {weld_x:.0f} m<extra></extra>"))
    if defects:
        fig.add_trace(go.Scatter3d(
            x=[d.distance_m for d in defects],
            y=[radius * 1.05 * np.cos(np.deg2rad(d.clock_position_deg)) for d in defects],
            z=[radius * 1.05 * np.sin(np.deg2rad(d.clock_position_deg)) for d in defects],
            mode="markers", marker=dict(size=6, color="#dc2626", symbol="diamond"),
            name="Anomalías de referencia",
            text=[f"{d.defect_id} · {d.defect_type}<br>{d.distance_m:.1f} m<br>Profundidad sintética: {d.depth_pct:.1f}%" for d in defects],
            hovertemplate="%{text}<extra></extra>"))
    fig.add_trace(go.Scatter3d(x=[pig_position_m], y=[0], z=[0], mode="markers+text",
                               marker=dict(size=10, color="#7c3aed", symbol="diamond"),
                               text=["PIG MFL"], textposition="top center", name="PIG MFL",
                               hovertemplate=f"PIG MFL<br>Posición: {pig_position_m:.1f} m<extra></extra>"))
    fig.update_layout(height=520, margin=dict(l=0, r=0, t=20, b=0),
                      scene=dict(xaxis_title="Distancia (m)", yaxis_title="Y (m)", zaxis_title="Z (m)",
                                 aspectmode="manual", aspectratio=dict(x=3, y=1, z=1)),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0))
    return fig
