"""AWS Lambda entrypoint for the housing regression inference pipeline."""

from __future__ import annotations

import base64
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import boto3
import pandas as pd

from src.inference_pipeline.inference import predict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

S3_BUCKET = os.environ.get("S3_BUCKET")
REGION_NAME = os.environ.get("REGION_NAME")
# These are the folders PATHS inside our S3 bucket (not our local project paths)
MODEL_KEY = os.environ.get("MODEL_KEY", "models/lgbm_model.pkl") # or models/lgbm_best_model.pkl
FREQ_ENCODER_KEY = os.environ.get("FREQ_ENCODER_KEY", "models/freq_encoder.pkl")
TARGET_ENCODER_KEY = os.environ.get("TARGET_ENCODER_KEY", "models/target_encoder.pkl")
TRAIN_FEATURES_KEY = os.environ.get("TRAIN_FEATURES_KEY", "processed/feature_engineered_train.csv")
ARTIFACT_DIR = Path(os.environ.get("ARTIFACT_DIR", "/tmp/ml_artifacts"))

if "AWS_LAMBDA_FUNCTION_NAME" not in os.environ:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

s3_client = boto3.client("s3", region_name= REGION_NAME)


def _ensure_local_artifact(key: str | None) -> Path | None:
    """Download an artifact from S3 the first time it is requested and reuse it afterwards."""
    if not key:
        return None

    local_path = ARTIFACT_DIR / Path(key)
    if not local_path.exists():
        local_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Downloading %s from bucket %s", key, S3_BUCKET)
        s3_client.download_file(S3_BUCKET, key, str(local_path))
    return local_path


def _parse_event(event: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract payload from an API Gateway proxy event and normalize to a list."""
    if "body" not in event:
        raise ValueError("Missing 'body' in request event")

    body = event["body"]
    if event.get("isBase64Encoded"):
        body = base64.b64decode(body)

    payload = json.loads(body)
    if isinstance(payload, dict):
        records = payload.get("records") or [payload]
    elif isinstance(payload, list):
        records = payload
    else:
        raise ValueError("Payload must be a JSON object or array")

    if not records:
        raise ValueError("No records provided in payload")

    return records


def _build_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    """AWS Lambda handler compatible with API Gateway proxy integration."""
    try:
        records = _parse_event(event)
        df = pd.DataFrame(records)
        if df.empty:
            raise ValueError("Request payload produced an empty DataFrame")

        model_path = _ensure_local_artifact(MODEL_KEY)
        if model_path is None or not model_path.exists():
            raise FileNotFoundError("Model file is not available locally")

        freq_path = _ensure_local_artifact(FREQ_ENCODER_KEY)
        target_path = _ensure_local_artifact(TARGET_ENCODER_KEY)
        train_path = _ensure_local_artifact(TRAIN_FEATURES_KEY)

        preds_df = predict(
            df,
            model_path=model_path,
            freq_encoder_path=freq_path,
            target_encoder_path=target_path,
            train_features_path=train_path,
        )

        response_body: Dict[str, Any] = {
            "predictions": preds_df["predicted_price"].astype(float).tolist(),
            "count": int(len(preds_df)),
        }
        if "actual_price" in preds_df.columns:
            response_body["actuals"] = preds_df["actual_price"].astype(float).tolist()

        return _build_response(200, response_body)

    except Exception as err:  # pylint: disable=broad-except
        logger.exception("Lambda inference failed")
        return _build_response(400, {"error": str(err)})