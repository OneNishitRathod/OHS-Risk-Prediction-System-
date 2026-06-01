# OHS Risk Prediction Platform

> AI-powered Occupational Health & Safety risk assessment for Ontario workplaces.
> Built for the **Data Analytics & Research Branch, Ontario Ministry of Labour, Immigration, Training and Skills Development**.

---

## Overview

This platform combines two chained machine learning models to predict workplace risk from OHS inspection data:

- **Model 1 — NLP Severity Classifier:** Reads an inspector's free-text narrative and classifies the incident as `Critical`, `High`, `Medium`, or `Low` severity using a SentenceTransformer + LogisticRegression pipeline.
- **Model 2 — Risk Score Predictor:** Takes 22 structured OHS fields plus Model 1's severity output and predicts a continuous workplace risk score from **0 to 100** using XGBoost.

Both models are trained and served on **Databricks Serverless**, tracked with **MLflow**, and exposed through a **Ministry-branded Flask web application**.

---

## Architecture

```
Inspector enters data
        │
        ▼
  Flask Web App (POST /predict)
        │
        ├──► Inspection Text ──► ohs-severity-endpoint (Databricks)
        │                              │
        │                         severity_level + confidence
        │                              │
        └──► Structured fields + severity_level
                       │
                       ▼
              ohs-risk-score-endpoint (Databricks)
                       │
               risk_score (0–100) + risk_category
                       │
                       ▼
              Results page rendered
```

---

## Model Performance

| Model | Algorithm | Key Metric |
|---|---|---|
| NLP Severity Classifier | SentenceTransformer (`all-MiniLM-L6-v2`) + LogisticRegression | **95% test accuracy** / 90% 5-fold CV |
| Risk Score Predictor | XGBoost Regressor (300 trees, lr=0.05) | **R²=0.772**, MAE=9.85 pts |

---

## Project Structure

```
├── databricks_notebooks/
│   ├── 01_data_generation.py       # Synthetic OHS data (500 records, Faker en_CA)
│   ├── 02_nlp_severity_model.py    # NLP model training + MLflow registration
│   ├── 03_risk_score_model.py      # XGBoost training + SHAP + MLflow registration
│   └── 04_model_serving.py         # Model promotion + endpoint testing
│
└── ohs_prediction_app/
    ├── run.py                       # Flask entry point
    ├── config.py                    # Config loaded from .env
    ├── requirements.txt
    ├── .env.example                 # Environment variable template
    ├── .gitignore
    └── app/
        ├── __init__.py              # App factory
        ├── routes.py                # GET / · POST /predict · GET /health
        ├── services/
        │   ├── severity_service.py  # Calls ohs-severity-endpoint
        │   └── risk_service.py      # Calls ohs-risk-score-endpoint
        ├── templates/
        │   ├── base.html            # Ministry-branded base layout
        │   ├── index.html           # 22-field inspection form
        │   └── result.html          # Dual-model results + risk gauge
        └── static/
            ├── css/style.css        # Ontario government colour system
            └── js/app.js            # Auto-fill, char counter, loading state
```

---

## Quickstart

### Prerequisites

- Python 3.10+
- A [Databricks](https://databricks.com/) workspace (free edition works)
- Both serving endpoints deployed and showing **Ready** (see Databricks Setup below)

---

### 1 — Databricks Setup

Import the four notebooks into your Databricks workspace and run them **in order**:

| # | Notebook | What it does | Est. runtime |
|---|---|---|---|
| 01 | `01_data_generation.py` | Generates 500 synthetic OHS records → Delta table `workspace.ohs_data.synthetic_inspections` | ~1 min |
| 02 | `02_nlp_severity_model.py` | Trains NLP model → registers `ohs_severity_classifier` in MLflow | ~5–8 min |
| 03 | `03_risk_score_model.py` | Trains XGBoost model → registers `ohs_risk_score_model` in MLflow | ~2–3 min |
| 04 | `04_model_serving.py` | Promotes both models to Production, tests REST endpoints | ~1 min |

**After notebook 02 and 03 complete**, create two serving endpoints in the Databricks UI:

> **Serving → Create serving endpoint**

| Endpoint name | Served entity | Compute |
|---|---|---|
| `ohs-severity-endpoint` | `ohs_severity_classifier` | Small, scale-to-zero |
| `ohs-risk-score-endpoint` | `ohs_risk_score_model` | Small, scale-to-zero |

Wait until both show **Ready** before running notebook 04 or the Flask app.

---

### 2 — Flask App Setup

```bash
# Clone the repo
git clone https://github.com/your-username/ohs-risk-prediction.git
cd ohs-risk-prediction/ohs_prediction_app

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
```

Open `.env` and fill in your values:

```env
DATABRICKS_HOST=https://your-workspace.azuredatabricks.net
DATABRICKS_TOKEN=dapi_your_personal_access_token_here

SEVERITY_ENDPOINT_URL=https://your-workspace.azuredatabricks.net/serving-endpoints/ohs-severity-endpoint/invocations
RISK_ENDPOINT_URL=https://your-workspace.azuredatabricks.net/serving-endpoints/ohs-risk-score-endpoint/invocations

USE_MOCK_PREDICTIONS=False
REQUEST_TIMEOUT=90
```

> **Where to find your PAT:** Databricks → top-right avatar → Settings → Developer → Access tokens → Generate new token

```bash
# Run the app
python run.py
```

Open **http://localhost:5000** in your browser.

---

### 3 — Testing Without Databricks

Set `USE_MOCK_PREDICTIONS=True` in your `.env` file. The app will use built-in domain-rule simulations and return realistic predictions without calling any endpoints — useful for UI development and demos.

---

## API Endpoints

| Route | Method | Description |
|---|---|---|
| `/` | GET | Inspection data entry form |
| `/predict` | POST | Runs both models, renders results |
| `/health` | GET | Returns `{"status": "ok"}` |

---

## Technology Stack

| Layer | Technology |
|---|---|
| NLP Embeddings | `sentence-transformers` — `all-MiniLM-L6-v2` (384-dim) |
| ML Model | XGBoost Regressor |
| Classifier | scikit-learn LogisticRegression |
| Explainability | SHAP TreeExplainer |
| Experiment Tracking | MLflow (Databricks managed) |
| Model Serving | Databricks Serverless Endpoints |
| Data Storage | Delta Lake, Unity Catalog |
| Web Framework | Flask 3.x |
| Synthetic Data | Faker (`en_CA` locale) |
| Frontend | Bootstrap 5, vanilla JS |

---

## Environment Variables Reference

| Variable | Required | Description |
|---|---|---|
| `DATABRICKS_HOST` | Yes | Your workspace URL (no trailing slash) |
| `DATABRICKS_TOKEN` | Yes | Personal Access Token |
| `SEVERITY_ENDPOINT_URL` | Yes | Full invocations URL for severity endpoint |
| `RISK_ENDPOINT_URL` | Yes | Full invocations URL for risk score endpoint |
| `USE_MOCK_PREDICTIONS` | No | `True` to bypass Databricks (default: `False`) |
| `REQUEST_TIMEOUT` | No | Seconds before endpoint timeout (default: `90`) |
| `SECRET_KEY` | No | Flask session key (change in production) |
| `FLASK_DEBUG` | No | Enable debug mode (default: `False`) |

---

## Notes

- **Catalog name:** All notebooks use the catalog name `workspace`. If your Databricks workspace uses a different catalog, find-and-replace `workspace.ohs_data` across all four notebooks before running.
- **Scale-to-zero cold start:** The first request after an idle period may take 30–60 seconds to warm up. This is normal behaviour on the free tier.
- **Synthetic data:** The models are trained on synthetic data generated to match the OHS dataset schema. Accuracy metrics reflect synthetic data performance. Retrain on real BOSTA/OHS inspection records for production use.
- **Never commit `.env`** — it contains your Databricks token. The `.gitignore` already excludes it.

---

## License

Ontario Ministry of Labour, Immigration, Training and Skills Development.
