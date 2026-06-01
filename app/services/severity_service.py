"""
app/services/severity_service.py
Calls the Databricks ohs-severity-endpoint and returns structured prediction.
"""
from __future__ import annotations
import json
import random
import requests


def predict_severity(
    inspection_text: str,
    endpoint_url: str,
    token: str,
    timeout: int = 90,
    use_mock: bool = False,
) -> tuple[dict | None, str | None]:
    """
    Returns (result_dict, error_message).
    result_dict keys: severity_level, confidence, probabilities
    """
    if use_mock or not endpoint_url or not token:
        return _mock_severity(inspection_text), None

    payload = {
        "dataframe_records": [
            {"inspection_text": inspection_text}
        ]
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type":  "application/json",
    }

    try:
        response = requests.post(
            endpoint_url,
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        data = response.json()

        # Databricks serving wraps output in {"predictions": [...]}
        predictions = data.get("predictions", data)
        if isinstance(predictions, list) and predictions:
            result = predictions[0]
        else:
            result = predictions

        return _normalize_severity(result), None

    except requests.exceptions.Timeout:
        return None, "Severity endpoint timed out. The model may be warming up — please retry."
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the Databricks severity endpoint. Check DATABRICKS_HOST in .env."
    except requests.exceptions.HTTPError as exc:
        return None, f"Severity endpoint returned HTTP {exc.response.status_code}: {exc.response.text[:300]}"
    except Exception as exc:          # noqa: BLE001
        return None, f"Unexpected error calling severity endpoint: {exc}"


def _normalize_severity(raw: dict) -> dict:
    """Ensure the dict has the expected keys regardless of minor schema changes."""
    return {
        "severity_level": raw.get("severity_level", "Unknown"),
        "confidence":     raw.get("confidence", 0.0),
        "probabilities":  raw.get("probabilities", {}),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Mock predictor — used when USE_MOCK_PREDICTIONS=true in .env
# Provides realistic outputs for UI development / testing without Databricks
# ─────────────────────────────────────────────────────────────────────────────

_KEYWORD_SEVERITY = {
    "fatal":       "Critical", "fatality":    "Critical", "death":       "Critical",
    "critical":    "Critical", "electrocution":"Critical", "buried":     "Critical",
    "stop work":   "High",     "asbestos":    "High",      "forklift":   "High",
    "fall":        "High",     "silica":      "High",      "explosion":  "Critical",
    "missing":     "Medium",   "incomplete":  "Medium",    "training":   "Medium",
    "overdue":     "Low",      "fading":      "Low",       "minor":      "Low",
}

def _mock_severity(text: str) -> dict:
    text_lower = text.lower()
    severity = "Medium"
    for keyword, level in _KEYWORD_SEVERITY.items():
        if keyword in text_lower:
            severity = level
            break

    # Build plausible probability distribution
    base = {"Critical": 0.05, "High": 0.15, "Medium": 0.55, "Low": 0.25}
    boost = {"Critical": 0.7, "High": 0.55, "Medium": 0.45, "Low": 0.6}

    probs: dict[str, float] = {}
    for k in base:
        probs[k] = base[k] + random.uniform(-0.03, 0.03)
    probs[severity] = boost[severity] + random.uniform(-0.05, 0.05)

    # Normalize
    total = sum(probs.values())
    probs = {k: round(v / total, 4) for k, v in probs.items()}

    return {
        "severity_level": severity,
        "confidence":     probs[severity],
        "probabilities":  probs,
    }
