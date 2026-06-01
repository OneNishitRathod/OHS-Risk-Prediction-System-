"""
app/routes.py — Route handlers
"""
from flask import Blueprint, render_template, request, current_app, redirect, url_for
from app.services.severity_service import predict_severity
from app.services.risk_service import predict_risk

main = Blueprint("main", __name__)

# ─── Dropdown option lists (matches Databricks training data domain) ─────────

FIELD_VISIT_TYPES = [
    "Field Visit",
    "Field Visit Support Role",
    "Offsite Visit",
]
CASE_TYPES = ["Inspection", "Investigation", "Consultation"]
CASE_STATUSES = ["Closed", "Open", "In Progress"]
CONTRAVENER_ROLES = [
    "Employer", "Constructor", "Supervisor", "Owner", "Worker", "Supplier",
]
ORDER_TYPES = [
    "Forthwith Order",
    "Time Based Order",
    "Stop Work Order",
    "Plan Order",
    "Time Unknown Order",
    "Requirement Forthwith",
    "Requirement Time Based",
]
ORDER_STATUSES = [
    "Complied With",
    "Not Complied With",
    "Outstanding",
    "In-Process",
    "Withdrawn/Cancelled",
    "Rescinded",
]
CASE_ACTS = [
    "Occupational Health and Safety Act",
    "Building Opportunities in the Skilled Trades Act",
]
REGULATIONS = [
    ("REG_851",  "Industrial Establishments"),
    ("REG_213",  "Construction Projects"),
    ("REG_490",  "Designated Substance - Asbestos on Construction Projects"),
    ("REG_632",  "Workplace Hazardous Materials Information System"),
    ("REG_297",  "Firefighters - Protective Equipment"),
    ("REG_O67",  "Occupational Health and Safety Act - General"),
    ("REG_854",  "Mines and Mining Plants"),
    ("REG_388",  "Electrical Utility Safety Rules"),
    ("REG_420",  "Notices and Reports - Fatalities and Critical Injuries"),
]
NAICS_OPTIONS = [
    ("236110", "Residential Building Construction"),
    ("236210", "Industrial Building Construction"),
    ("237110", "Water and Sewer Line Construction"),
    ("238110", "Poured Concrete Foundation Contractors"),
    ("238210", "Electrical Contractors and Other Wiring Installation"),
    ("238310", "Drywall and Insulation Contractors"),
    ("311511", "Fluid Milk Manufacturing"),
    ("321111", "Sawmills"),
    ("331110", "Iron and Steel Mills"),
    ("332310", "Prefabricated Metal Building Manufacturing"),
    ("335930", "Wiring Device Manufacturing"),
    ("621110", "Offices of Physicians"),
    ("622110", "General Medical and Surgical Hospitals"),
    ("623110", "Nursing Care Facilities"),
    ("212110", "Bituminous Coal Underground Mining"),
    ("212220", "Gold and Silver Ore Mining"),
    ("212315", "Limestone Quarrying and Processing"),
    ("722511", "Full-Service Restaurants"),
    ("811111", "General Automotive Repair"),
    ("337110", "Wood Kitchen Cabinet Manufacturing"),
]
SECTIONS    = ["25", "26", "27", "28", "29", "43", "50", "54", "55", "57"]
SUBSECTIONS = ["", "(1)", "(2)", "(3)", "(4)", "(5)"]
CLAUSES     = ["", "(a)", "(b)", "(c)", "(d)", "(e)", "(f)"]


def _build_form_context() -> dict:
    """Shared dropdown data for the form template."""
    return dict(
        field_visit_types=FIELD_VISIT_TYPES,
        case_types=CASE_TYPES,
        case_statuses=CASE_STATUSES,
        contravener_roles=CONTRAVENER_ROLES,
        order_types=ORDER_TYPES,
        order_statuses=ORDER_STATUSES,
        case_acts=CASE_ACTS,
        regulations=REGULATIONS,
        naics_options=NAICS_OPTIONS,
        sections=SECTIONS,
        subsections=SUBSECTIONS,
        clauses=CLAUSES,
    )


# ─────────────────────────────────────────────────────────────────────────────

@main.route("/", methods=["GET"])
def index():
    return render_template("index.html", **_build_form_context())


@main.route("/predict", methods=["POST"])
def predict():
    """
    Prediction pipeline:
      1. Collect form data
      2. Call Severity endpoint  (NLP model — text description)
      3. Pass severity to Risk endpoint (ML model — structured data + severity)
      4. Render results
    """
    form = request.form

    # ── Collect inputs ────────────────────────────────────────────────────────
    inspection_text = form.get("inspection_text", "").strip()

    structured = {
        "FIELD_VISIT_DATE":  form.get("field_visit_date", ""),
        "FIELD_VISIT_TYPE":  form.get("field_visit_type", ""),
        "CASE_TYPE":         form.get("case_type", ""),
        "CASE_STATUS":       form.get("case_status", ""),
        "WORKPLACE_ID":      form.get("workplace_id", ""),
        "WORKPLACE_NAME_AT_FV_TIME":    form.get("workplace_name", ""),
        "WORKPLACE_ADDRESS_AT_FV_TIME": form.get("workplace_address", ""),
        "POSTAL_CODE":       form.get("postal_code", ""),
        "PRIMARY_NAICS":     form.get("primary_naics", ""),
        "NAICS_DESCRIPTION": form.get("naics_description", ""),
        "CONTRAVENER_ROLE":  form.get("contravener_role", ""),
        "CONTRAVENER_ORG_ID": form.get("contravener_org_id", ""),
        "CONTRAVENER_NAME":  form.get("contravener_name", ""),
        "ORDER_TYPE":        form.get("order_type", ""),
        "ORDER_STATUS":      form.get("order_status", ""),
        "CASE_ACT":          form.get("case_act", ""),
        "ACT_REG_ID":        form.get("act_reg_id", ""),
        "ACT_REGULATION_NAME": form.get("act_regulation_name", ""),
        "SEC":               form.get("sec", ""),
        "SUBSEC":            form.get("subsec", ""),
        "CLAUSE":            form.get("clause", ""),
    }

    use_mock = current_app.config.get("USE_MOCK_PREDICTIONS", False)

    # ── Step 1: NLP Severity Prediction ──────────────────────────────────────
    sev_result, sev_error = predict_severity(
        inspection_text=inspection_text,
        endpoint_url=current_app.config["SEVERITY_ENDPOINT_URL"],
        token=current_app.config["DATABRICKS_TOKEN"],
        timeout=current_app.config["REQUEST_TIMEOUT"],
        use_mock=use_mock,
    )

    # ── Step 2: Risk Score Prediction (injects severity from Model 1) ─────────
    if sev_result:
        structured["SEVERITY_LEVEL"] = sev_result.get("severity_level", "Medium")

    risk_result, risk_error = predict_risk(
        structured_data=structured,
        endpoint_url=current_app.config["RISK_ENDPOINT_URL"],
        token=current_app.config["DATABRICKS_TOKEN"],
        timeout=current_app.config["REQUEST_TIMEOUT"],
        use_mock=use_mock,
    )

    return render_template(
        "result.html",
        # Inputs
        inspection_text=inspection_text,
        structured=structured,
        # Model 1 results
        severity_result=sev_result,
        severity_error=sev_error,
        # Model 2 results
        risk_result=risk_result,
        risk_error=risk_error,
        # Form options for "Predict Another" back-link
        **_build_form_context(),
    )


@main.route("/health")
def health():
    return {"status": "ok", "service": "OHS Risk Prediction API"}, 200
