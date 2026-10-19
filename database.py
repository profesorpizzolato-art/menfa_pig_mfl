import sqlite3
import json
from pathlib import Path
import pandas as pd

DB_PATH = Path(__file__).resolve().parent / "menfa_pig_mfl.db"

def _connect():
    return sqlite3.connect(DB_PATH)

def init_db():
    with _connect() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            duct_id TEXT NOT NULL,
            scenario TEXT NOT NULL,
            length_km REAL,
            diameter_mm INTEGER,
            wall_mm REAL,
            speed_m_s REAL,
            channels INTEGER,
            seed INTEGER,
            detected_count INTEGER,
            reference_count INTEGER,
            invalid_channels INTEGER,
            config_json TEXT
        )
        """)

def save_run(config, summary):
    with _connect() as con:
        con.execute("""
        INSERT INTO runs (duct_id, scenario, length_km, diameter_mm, wall_mm, speed_m_s,
        channels, seed, detected_count, reference_count, invalid_channels, config_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            config["duct_id"], config["scenario"], config["length_km"], config["diameter_mm"],
            config["wall_mm"], config["speed_m_s"], config["channels"], config["seed"],
            summary["detected_count"], summary["reference_count"], summary["invalid_channels"],
            json.dumps(config, ensure_ascii=False)
        ))

def list_runs():
    with _connect() as con:
        return pd.read_sql_query("""
        SELECT id, created_at, duct_id, scenario, length_km, diameter_mm, wall_mm,
        speed_m_s, channels, detected_count, reference_count, invalid_channels, seed
        FROM runs ORDER BY id DESC
