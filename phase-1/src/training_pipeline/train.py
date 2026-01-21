"""
Train a baseline LightGBM model.

- Reads feature-engineered train/eval CSVs.
- Trains LGBMRegressor.
- Returns metrics and saves model to `model_output`.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Optional

import numpy as np
import pandas as pd
from joblib import dump
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from lightgbm import LGBMRegressor

DEFAULT_TRAIN = Path("data/processed/feature_engineered_train.csv")
DEFAULT_EVAL = Path("data/processed/feature_engineered_eval.csv")
DEFAULT_OUT = Path("data/models/lgbm_model.pkl")


def _maybe_sample(df: pd.DataFrame, sample_frac: Optional[float], random_state: int) -> pd.DataFrame:
    if sample_frac is None:
        return df
    sample_frac = float(sample_frac)
    if sample_frac <= 0 or sample_frac >= 1:
        return df
    return df.sample(frac=sample_frac, random_state=random_state).reset_index(drop=True)


def train_model(
    train_path: Path | str = DEFAULT_TRAIN,
    eval_path: Path | str = DEFAULT_EVAL,
    model_output: Path | str = DEFAULT_OUT,
    model_params: Optional[Dict] = None,
    sample_frac: Optional[float] = None,
    random_state: int = 42,
):
    """Train baseline LightGBM and save model.

    Returns
    -------
    model : LGBMRegressor
    metrics : dict[str, float]
    """
    train_df = pd.read_csv(train_path)
    eval_df = pd.read_csv(eval_path)

    train_df = _maybe_sample(train_df, sample_frac, random_state)
    eval_df = _maybe_sample(eval_df, sample_frac, random_state)

    target = "price"
    X_train, y_train = train_df.drop(columns=[target]), train_df[target]
    X_eval, y_eval = eval_df.drop(columns=[target]), eval_df[target]

    params = {
        "n_estimators": 600,
        "learning_rate": 0.05,
        "num_leaves": 64,
        "max_depth": -1,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_samples": 20,
        "reg_alpha": 0.0,
        "reg_lambda": 0.0,
        "random_state": random_state,
        "n_jobs": -1,
        "verbosity": -1,
    }
    if model_params:
        params.update(model_params)

    model = LGBMRegressor(**params)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_eval)
    mae = float(mean_absolute_error(y_eval, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_eval, y_pred)))
    r2 = float(r2_score(y_eval, y_pred))
    metrics = {"mae": mae, "rmse": rmse, "r2": r2}

    out = Path(model_output)
    if "AWS_LAMBDA_FUNCTION_NAME" not in os.environ:
        out.parent.mkdir(parents=True, exist_ok=True)
    dump(model, out)
    print(f"✅ Model trained. Saved to {out}")
    print(f"   MAE={mae:.2f}  RMSE={rmse:.2f}  R²={r2:.4f}")

    return model, metrics


if __name__ == "__main__":
    train_model()
