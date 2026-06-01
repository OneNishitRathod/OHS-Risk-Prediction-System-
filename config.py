"""
config.py — Application configuration loaded from .env
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Flask
    SECRET_KEY  = os.getenv("SECRET_KEY", "ohs-dev-secret-change-in-prod")
    DEBUG       = os.getenv("FLASK_DEBUG", "False").lower() == "true"

    # Databricks
    DATABRICKS_HOST  = os.getenv("DATABRICKS_HOST", "").rstrip("/")
    DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")

    # Serving endpoints — can be set explicitly or auto-built from host
    SEVERITY_ENDPOINT_URL = os.getenv(
        "SEVERITY_ENDPOINT_URL",
        f"{DATABRICKS_HOST}/serving-endpoints/ohs-severity-endpoint/invocations",
    )
    RISK_ENDPOINT_URL = os.getenv(
        "RISK_ENDPOINT_URL",
        f"{DATABRICKS_HOST}/serving-endpoints/ohs-risk-score-endpoint/invocations",
    )

    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "90"))  # seconds

    # Set USE_MOCK_PREDICTIONS=true in .env to bypass Databricks during UI testing
    USE_MOCK_PREDICTIONS = os.getenv("USE_MOCK_PREDICTIONS", "False").lower() == "true"
