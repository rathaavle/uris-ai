#!/usr/bin/env python3
"""
Task 23 — Training FloodRiskEngine dengan data real.

Strategi: aggregate per region (bukan per hari) karena data cuaca BMKG
adalah prakiraan masa depan, sementara data banjir adalah historis masa lalu.
Label = apakah region ini termasuk daerah rawan banjir (flood_count > 0).

Output:
- models/flood_risk_model.pkl
- models/flood_risk_scaler.pkl
- models/flood_risk_metadata.json

Usage:
    python scripts/train_flood_model.py
"""

import sys
import json
import logging
import pickle
from pathlib import Path
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import LeaveOneOut, cross_val_score
from sklearn.metrics import f1_score
from sqlalchemy import text

from uris_ai.config import settings
from uris_ai.models.db_utils import create_db_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger(__name__)

MODELS_DIR = Path(__file__).parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

FEATURE_COLS = [
    "avg_rainfall", "max_rainfall", "avg_humidity",
    "avg_temperature", "avg_wind",
    "elevation", "drainage_capacity",
    "flood_count", "avg_severity",
]


def load_data(engine) -> tuple[pd.DataFrame, pd.DataFrame]:
    log.info("  Memuat data cuaca dari MySQL...")
    weather_df = pd.read_sql("""
        SELECT w.region_id, w.rainfall, w.humidity, w.temperature,
               COALESCE(w.wind_speed, 0) as wind_speed,
               r.elevation, r.drainage_capacity
        FROM weather_data w
        JOIN regions r ON w.region_id = r.region_id
    """, engine)
    log.info(f"  ✓ {len(weather_df)} baris cuaca")

    log.info("  Memuat data historis banjir...")
    flood_df = pd.read_sql("""
        SELECT region_id, severity, water_level FROM flood_events
    """, engine)
    log.info(f"  ✓ {len(flood_df)} baris banjir")
    return weather_df, flood_df


def build_features(weather_df: pd.DataFrame, flood_df: pd.DataFrame) -> pd.DataFrame:
    log.info("  Membangun feature matrix (agregat per region)...")

    weather_agg = weather_df.groupby("region_id").agg(
        avg_rainfall=("rainfall", "mean"),
        max_rainfall=("rainfall", "max"),
        avg_humidity=("humidity", "mean"),
        avg_temperature=("temperature", "mean"),
        avg_wind=("wind_speed", "mean"),
        elevation=("elevation", "first"),
        drainage_capacity=("drainage_capacity", "first"),
    ).reset_index()

    flood_stats = flood_df.groupby("region_id").agg(
        flood_count=("severity", "count"),
        avg_severity=("severity", "mean"),
    ).reset_index()

    df = weather_agg.merge(flood_stats, on="region_id", how="left")
    df["flood_count"] = df["flood_count"].fillna(0)
    df["avg_severity"] = df["avg_severity"].fillna(0)

    # Label: flood_prone = 1 jika region pernah banjir
    df["flood_prone"] = (df["flood_count"] > 0).astype(int)

    log.info(f"  ✓ {len(df)} regions, label: {df['flood_prone'].value_counts().to_dict()}")
    return df


def train_model(df: pd.DataFrame) -> dict:
    log.info("  Training RandomForest model...")

    X = df[FEATURE_COLS].values
    y = df["flood_prone"].values

    scaler = StandardScaler()
    X_s = scaler.fit_transform(X)

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=6,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
    )

    # Leave-One-Out CV karena dataset kecil (25 regions)
    loo = LeaveOneOut()
    cv_scores = cross_val_score(model, X_s, y, cv=loo, scoring="f1")
    f1 = float(cv_scores.mean())
    log.info(f"  F1 LOO-CV: {f1:.4f} (±{cv_scores.std():.4f})")

    # Train on full data
    model.fit(X_s, y)

    feat_importance = dict(zip(FEATURE_COLS, model.feature_importances_.tolist()))
    top_features = sorted(feat_importance.items(), key=lambda x: x[1], reverse=True)[:3]
    log.info(f"  Top features: {[f[0] for f in top_features]}")

    return {
        "model": model,
        "scaler": scaler,
        "f1_score": f1,
        "feature_importance": feat_importance,
        "top_features": [f[0] for f in top_features],
        "n_samples": len(df),
        "positive_ratio": float(y.mean()),
    }


def save_model(results: dict) -> None:
    with open(MODELS_DIR / "flood_risk_model.pkl", "wb") as f:
        pickle.dump(results["model"], f)
    with open(MODELS_DIR / "flood_risk_scaler.pkl", "wb") as f:
        pickle.dump(results["scaler"], f)

    metadata = {
        "version": "1.0.0",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "f1_score": results["f1_score"],
        "feature_importance": results["feature_importance"],
        "top_features": results["top_features"],
        "feature_cols": FEATURE_COLS,
        "n_samples": results["n_samples"],
        "positive_ratio": results["positive_ratio"],
        "algorithm": "RandomForestClassifier",
        "status": "active",
    }
    with open(MODELS_DIR / "flood_risk_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)

    log.info(f"  ✓ Model, scaler, metadata disimpan di models/")


def update_risk_scores(engine, model, scaler, df: pd.DataFrame) -> int:
    log.info("  Memperbarui risk_scores dengan prediksi ML...")
    now = datetime.now(timezone.utc)

    # Prediksi probabilitas untuk setiap region
    X = df[FEATURE_COLS].values
    X_s = scaler.transform(X)

    # Handle model yang hanya punya 1 kelas
    try:
        flood_probs = model.predict_proba(X_s)[:, 1]
    except IndexError:
        # Fallback jika hanya 1 kelas: pakai decision function
        flood_probs = (model.predict(X_s) == 1).astype(float)

    count = 0
    with engine.connect() as conn:
        for i, row in df.iterrows():
            flood_risk = float(flood_probs[i]) * 100
            elevation = float(row.get("elevation", 10))
            drainage = float(row.get("drainage_capacity", 150))
            flood_hist = float(row.get("flood_count", 0))

            # Boost flood_risk berdasarkan karakteristik geografis
            geo_boost = max(0, (20 - min(elevation, 20)) * 1.5 + (150 - min(drainage, 150)) * 0.15)
            flood_risk = min(95, flood_risk + geo_boost)

            # Traffic dan service berbasis flood_risk
            traffic = max(5, min(95, flood_risk * 0.65))
            service = max(5, min(95, flood_risk * 0.40))
            urs = round(flood_risk * 0.5 + traffic * 0.3 + service * 0.2, 2)

            conn.execute(text("""
                UPDATE risk_scores
                SET flood_risk = :fr, traffic_impact = :ti,
                    service_access = :sa, urban_risk_score = :urs, date = :dt
                WHERE region_id = :rid
            """), {
                "fr": round(flood_risk, 2),
                "ti": round(traffic, 2),
                "sa": round(service, 2),
                "urs": urs,
                "dt": now,
                "rid": int(row["region_id"]),
            })
            count += 1
        conn.commit()

    log.info(f"  ✓ {count} risk_scores diperbarui")
    return count


def main():
    log.info("╔══════════════════════════════════════════════╗")
    log.info("║  URIS-AI — Training Flood Risk Model         ║")
    log.info("╚══════════════════════════════════════════════╝")

    engine = create_db_engine(settings.azure_mysql_connection_string)

    log.info("── Step 1: Load data ─────────────────────────")
    weather_df, flood_df = load_data(engine)

    log.info("── Step 2: Build features ────────────────────")
    df = build_features(weather_df, flood_df)

    log.info("── Step 3: Train model ───────────────────────")
    results = train_model(df)

    log.info("── Step 4: Save model ────────────────────────")
    save_model(results)

    log.info("── Step 5: Update risk scores ────────────────")
    updated = update_risk_scores(engine, results["model"], results["scaler"], df)

    log.info("")
    log.info("══ SELESAI ══════════════════════════════════")
    log.info(f"  F1-score (LOO-CV) : {results['f1_score']:.4f}")
    log.info(f"  Top features      : {results['top_features']}")
    log.info(f"  Risk scores       : {updated} diperbarui")
    if results["f1_score"] >= 0.75:
        log.info("  ✅ F1 >= 0.75 — memenuhi requirement Req 1.2")
    else:
        log.warning("  ⚠️  F1 < 0.75 — perlu data historis banjir lebih banyak")
    log.info("═════════════════════════════════════════════")


if __name__ == "__main__":
    main()
