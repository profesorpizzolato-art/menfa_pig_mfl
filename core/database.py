"""SQLite storage for educational simulation runs."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from typing import Any

DEFAULT_DB = Path(__file__).resolve().parent / "menfa_pig_mfl.db"


def connect(db_path: str | Path = DEFAULT_DB) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def initialize(db_path: str | Path = DEFAULT_DB) -> None:
    with connect(db_path) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            operator TEXT NOT NULL,
            scenario TEXT NOT NULL,
            seed INTEGER NOT NULL,
            length_m REAL NOT NULL,
            speed_m_s REAL NOT NULL,
            channels INTEGER NOT NULL,
            reference_defects INTEGER NOT NULL,
            detected_indications INTEGER NOT NULL,
            threshold REAL NOT NULL,
            metadata_json TEXT NOT NULL
        )""")


def save_run(run: dict[str, Any], db_path: str | Path = DEFAULT_DB) -> int:
    initialize(db_path)
    with connect(db_path) as conn:
        cur = conn.execute("""INSERT INTO runs
            (created_at, operator, scenario, seed, length_m, speed_m_s, channels,
             reference_defects, detected_indications, threshold, metadata_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (datetime.now(timezone.utc).isoformat(timespec="seconds"),
             str(run.get("operator", "Operador MENFA")), str(run["scenario"]), int(run["seed"]),
             float(run["length_m"]), float(run["speed_m_s"]), int(run["channels"]),
             int(run["reference_defects"]), int(run["detected_indications"]), float(run["threshold"]),
             json.dumps(run.get("metadata", {}), ensure_ascii=False)))
        return int(cur.lastrowid)


def list_runs(db_path: str | Path = DEFAULT_DB, limit: int = 100):
    initialize(db_path)
    with connect(db_path) as conn:
        rows = conn.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
    return [dict(row) for row in rows]


def clear_runs(db_path: str | Path = DEFAULT_DB) -> None:
    with connect(db_path) as conn:
        conn.execute("DELETE FROM runs")
