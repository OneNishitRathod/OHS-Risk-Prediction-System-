"""
app/services/risk_service.py
Calls the Databricks ohs-risk-score-endpoint and returns structured prediction.
"""
from __future__ import annotations
import random
import requests


def predict_risk(
    structured_data: dict,
    endpoint_url: str,
    token: str,
    timeout: int = 90,
    use_mock: bool = False,
) -> tuple[dict | None, str | None]:
    """
    Returns (result_dict, error_message).
    result_dict keys: risk_score, risk_category, risk_level_int
    """
    if use_mock or not endpoint_url or not token:
        return _mock_risk(structured_data), None

    payload = {"dataframe_records": [structured_data]}
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

        predictions = data.get("predictions", data)
        if isinstance(predictions, list) and predictions:
            result = predictions[0]
        else:
            result = predictions

        return _normalize_risk(result), None

    except requests.exceptions.Timeout:
        return None, "Risk endpoint timed out. The model may be warming up — please retry."
    except requests.exceptions.ConnectionError:
        return None, "Could not reach the Databricks risk endpoint. Check DATABRICKS_HOST in .env."
    except requests.exceptions.HTTPError as exc:
        return None, f"Risk endpoint returned HTTP {exc.response.status_code}: {exc.response.text[:300]}"
    except Exception as exc:          # noqa: BLE001
        return None, f"Unexpected error calling risk endpoint: {exc}"


def _normalize_risk(raw: dict) -> dict:
    score = float(raw.get("risk_score", 0))
    if   score >= 75: cat, lvl = "Critical Risk", 4
    elif score >= 55: cat, lvl = "High Risk",     3
    elif score >= 35: cat, lvl = "Medium Risk",   2
    else:             cat, lvl = "Low Risk",      1
    return {
        "risk_score":     round(score, 1),
        "risk_category":  raw.get("risk_category",  cat),
        "risk_level_int": raw.get("risk_level_int", lvl),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Mock predictor
# ─────────────────────────────────────────────────────────────────────────────

_HIGH_RISK_ORDERS   = {"Stop Work Order", "Plan Order", "Time Unknown Order"}
_SEVERITY_BASE      = {"Critical": 82, "High": 62, "Medium": 38, "Low": 16}
_ORDER_ADJ          = {
    "Stop Work Order": 12, "Plan Order": 6, "Time Unknown Order": 8,
    "Time Based Order": 3, "Forthwith Order": -2,
    "Requirement Time Based": 1, "Requirement Forthwith": -3,
}
_STATUS_ADJ = {
    "Not Complied With": 14, "Outstanding": 9, "In-Process": 2,
    "Complied With": -8, "Withdrawn/Cancelled": -5, "Rescinded": -3,
}
_SECTOR_ADJ = {"Construction": 6, "Mining": 9, "Health Care": 4, "Industrial": 2}


def _get_sector(naics: str) -> str:
    n = str(naics)
    if n.startswith("23"): return "Construction"
    if n.startswith("21"): return "Mining"
    if n.startswith("6"):  return "Health Care"
    return "Industrial"


def _mock_risk(data: dict) -> dict:
    severity    = data.get("SEVERITY_LEVEL", "Medium")
    order_type  = data.get("ORDER_TYPE", "Forthwith Order")
    order_status= data.get("ORDER_STATUS", "In-Process")
    case_type   = data.get("CASE_TYPE", "Inspection")
    naics       = data.get("PRIMARY_NAICS", "722511")

    base   = _SEVERITY_BASE.get(severity, 38)
    score  = (
        base
        + _ORDER_ADJ.get(order_type, 0)
        + _STATUS_ADJ.get(order_status, 0)
        + (6 if case_type == "Investigation" else 0)
        + _SECTOR_ADJ.get(_get_sector(naics), 2)
        + random.gauss(0, 5)
    )
    score = round(min(100.0, max(0.0, score)), 1)

    if   score >= 75: cat, lvl = "Critical Risk", 4
    elif score >= 55: cat, lvl = "High Risk",     3
    elif score >= 35: cat, lvl = "Medium Risk",   2
    else:             cat, lvl = "Low Risk",      1

    return {"risk_score": score, "risk_category": cat, "risk_level_int": lvl}
