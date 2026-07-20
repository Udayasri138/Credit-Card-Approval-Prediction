"""
app.py
======
Credit Card Approval Prediction System — Flask Application
"""

import os
import io
import csv
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, flash, jsonify, Response, abort
)
from werkzeug.security import generate_password_hash, check_password_hash
import mysql.connector
from mysql.connector import Error

from config import Config

# ─────────────────────────────────────────────
# App initialisation
# ─────────────────────────────────────────────
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = Config.SECRET_KEY

os.makedirs(Config.MODELS_DIR, exist_ok=True)
os.makedirs(Config.EXPORT_FOLDER, exist_ok=True)


# ─────────────────────────────────────────────
# Database helpers
# ─────────────────────────────────────────────
def get_db():
    """Return a new MySQL connection."""
    return mysql.connector.connect(
        host=Config.DB_HOST,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        database=Config.DB_NAME,
        port=Config.DB_PORT,
        charset="utf8mb4",
        autocommit=False,
    )


def query_db(sql: str, args=(), one=False, commit=False):
    """Execute a parameterised query and return results."""
    conn = get_db()
    cur  = conn.cursor(dictionary=True)
    try:
        cur.execute(sql, args)
        if commit:
            conn.commit()
            return cur.lastrowid
        rv = cur.fetchone() if one else cur.fetchall()
        return rv
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


# ─────────────────────────────────────────────
# ML Model cache
# ─────────────────────────────────────────────
_pipeline_cache = None

def load_pipeline():
    """Load model pipeline from disk (cached)."""
    global _pipeline_cache
    if _pipeline_cache is None:
        if not os.path.exists(Config.MODEL_PATH):
            return None
        _pipeline_cache = joblib.load(Config.MODEL_PATH)
    return _pipeline_cache


# ─────────────────────────────────────────────
# Auth decorators
# ─────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in.", "warning")
            return redirect(url_for("login"))
        if session.get("role") != "admin":
            abort(403)
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────
# Seed admin + ML model records on first run
# ─────────────────────────────────────────────
def seed_database():
    """Create admin user and ML model records if they don't exist."""
    try:
        # Admin user
        existing = query_db(
            "SELECT UserID FROM Users WHERE Email = %s", (Config.ADMIN_EMAIL,), one=True
        )
        if not existing:
            query_db(
                "INSERT INTO Users (Name, Email, Password, Role) VALUES (%s, %s, %s, 'admin')",
                (Config.ADMIN_NAME, Config.ADMIN_EMAIL,
                 generate_password_hash(Config.ADMIN_PASSWORD)),
                commit=True,
            )
            print(f"[SEED] Admin created: {Config.ADMIN_EMAIL}")

        # ML model records
        count = query_db("SELECT COUNT(*) as c FROM ML_Model", one=True)
        if count and count["c"] == 0:
            metrics_path = os.path.join(Config.MODELS_DIR, "metrics.json")
            if os.path.exists(metrics_path):
                with open(metrics_path) as f:
                    metrics = json.load(f)
                for m in metrics:
                    query_db(
                        """INSERT INTO ML_Model
                           (ModelName, AlgorithmType, Accuracy, Precision_Score,
                            Recall_Score, F1_Score, ROC_AUC, ModelFile, IsBestModel)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (m["model_name"], m["algorithm_type"], m["accuracy"],
                         m["precision"], m["recall"], m["f1"], m["roc_auc"],
                         m["model_file"], 1 if m["is_best"] else 0),
                        commit=True,
                    )
                print("[SEED] ML model records inserted.")
    except Error as e:
        print(f"[SEED ERROR] {e}")


# ─────────────────────────────────────────────
# Prediction helper
# ─────────────────────────────────────────────
INCOME_TYPE_MAP  = {
    "Working": 0, "Commercial associate": 1, "Pensioner": 2,
    "State servant": 3, "Student": 4
}
EDUCATION_MAP = {
    "Higher education": 0, "Secondary / secondary special": 1,
    "Incomplete higher": 2, "Lower secondary": 3, "Academic degree": 4
}
FAMILY_STATUS_MAP = {
    "Married": 0, "Single / not married": 1, "Civil marriage": 2,
    "Separated": 3, "Widow": 4
}
HOUSING_MAP = {
    "House / apartment": 0, "With parents": 1, "Municipal apartment": 2,
    "Rented apartment": 3, "Office apartment": 4, "Co-op apartment": 5
}
GENDER_MAP = {"Male": 0, "M": 0, "Female": 1, "F": 1, "Other": 2}
AGE_BIN_MAP = {"21-30": 0, "31-40": 1, "41-50": 2, "51-60": 3, "61-70": 4}
INCOME_BIN_MAP = {"Low": 0, "Medium": 1, "High": 2, "Very High": 3}


def build_feature_vector(form: dict) -> np.ndarray:
    """Convert form dict to numpy feature array matching training feature order."""
    gender         = int(GENDER_MAP.get(form.get("gender", "Male"), 0))
    owns_car       = 1 if form.get("owns_car") in ["on", 1, "1"] else 0
    owns_property  = 1 if form.get("owns_property") in ["on", 1, "1"] else 0
    num_children   = int(form.get("num_children", 0))
    annual_income  = float(form.get("annual_income", 300000))
    income_type    = int(INCOME_TYPE_MAP.get(form.get("income_type", "Working"), 0))
    edu_type       = int(EDUCATION_MAP.get(form.get("education_type", "Higher education"), 0))
    fam_status     = int(FAMILY_STATUS_MAP.get(form.get("family_status", "Married"), 0))
    housing_type   = int(HOUSING_MAP.get(form.get("housing_type", "House / apartment"), 0))
    age            = int(form.get("age", 35))
    emp_days       = int(form.get("employment_days", 1000))
    work_phone     = 1 if form.get("work_phone_provided") in ["on", 1, "1"] else 0
    phone          = 1 if form.get("phone_provided") in ["on", 1, "1"] else 0
    email          = 1 if form.get("email_provided") in ["on", 1, "1"] else 0
    family_count   = int(form.get("family_member_count", 1))
    months_balance = int(form.get("months_balance", -12))
    overdue_months = int(form.get("overdue_months", 0))
    is_employed    = 1 if emp_days > 0 else 0
    income_per_mem = annual_income / max(family_count, 1)

    # AgeBin: 21-30=0, 31-40=1, 41-50=2, 51-60=3, 61-70=4
    age_bin = min(max((age - 21) // 10, 0), 4)

    # IncomeBin: quartile approximation
    if annual_income < 150000:
        income_bin = 0
    elif annual_income < 300000:
        income_bin = 1
    elif annual_income < 600000:
        income_bin = 2
    else:
        income_bin = 3

    emp_years      = abs(emp_days) / 365.0
    high_risk_od   = 1 if overdue_months >= 2 else 0

    feature_vector = np.array([[
        gender, owns_car, owns_property, num_children, annual_income,
        income_type, edu_type, fam_status, housing_type, age,
        emp_days, work_phone, phone, email, family_count,
        months_balance, overdue_months, is_employed, income_per_mem,
        age_bin, income_bin, emp_years, high_risk_od,
    ]], dtype=float)

    return feature_vector


def get_risk_category(prob: float) -> str:
    if prob >= 0.75:
        return "Low Risk"
    elif prob >= 0.45:
        return "Medium Risk"
    else:
        return "High Risk"


def calculate_feature_impacts(form: dict, prob: float) -> list:
    """Calculate positive/negative feature impacts dynamically for explainable AI (XAI)."""
    impacts = []

    # 1. Income Impact
    try:
        income = float(form.get("annual_income") or form.get("AnnualIncome") or 300000)
    except (ValueError, TypeError):
        income = 300000

    if income >= 500000:
        impacts.append({
            "name": "Annual Income",
            "type": "positive",
            "effect": "High Positive",
            "desc": f"Annual income of ₹{income:,.2f} provides exceptional loan repayment capacity."
        })
    elif income >= 200000:
        impacts.append({
            "name": "Annual Income",
            "type": "positive",
            "effect": "Moderate Positive",
            "desc": f"Income of ₹{income:,.2f} safely meets core qualification benchmarks."
        })
    else:
        impacts.append({
            "name": "Annual Income",
            "type": "negative",
            "effect": "Moderate Negative",
            "desc": f"Lower income scale (₹{income:,.2f}) heightens credit delinquency safety margins."
        })

    # 2. Credit Overdue History Impact
    try:
        overdue_val = form.get("overdue_months")
        if overdue_val is None:
            # Try reconstruct from PaymentStatus
            ps = form.get("PaymentStatus", "C")
            overdue_months = int(ps) if ps in ['0','1','2','3','4','5'] else 0
        else:
            overdue_months = int(overdue_val)
    except (ValueError, TypeError):
        overdue_months = 0

    if overdue_months >= 2:
        impacts.append({
            "name": "Credit Delinquencies",
            "type": "negative",
            "effect": "Critical Negative",
            "desc": f"Serious credit delays ({overdue_months} months overdue) heavily flag active delinquency risk."
        })
    elif overdue_months == 1:
        impacts.append({
            "name": "Credit Delinquencies",
            "type": "negative",
            "effect": "Moderate Negative",
            "desc": "Active minor overdue history (1 month overdue) reduces credit eligibility score."
        })
    else:
        impacts.append({
            "name": "Credit Delinquencies",
            "type": "positive",
            "effect": "High Positive",
            "desc": "Flawless repayment history with zero active overdue months."
        })

    # 3. Job Tenure Impact
    try:
        emp_days = int(form.get("employment_days") or form.get("EmploymentDays") or 1000)
    except (ValueError, TypeError):
        emp_days = 1000

    if emp_days > 1825:
        impacts.append({
            "name": "Employment Tenure",
            "type": "positive",
            "effect": "High Positive",
            "desc": f"Excellent career stability with {emp_days // 365} years of continuous employment."
        })
    elif emp_days > 365:
        impacts.append({
            "name": "Employment Tenure",
            "type": "positive",
            "effect": "Moderate Positive",
            "desc": f"Steady employment history of {emp_days // 365} year(s)."
        })
    elif emp_days < 0:
        impacts.append({
            "name": "Employment Tenure",
            "type": "negative",
            "effect": "High Negative",
            "desc": f"Currently unemployed ({abs(emp_days) // 30} months) impacts steady income score."
        })
    else:
        impacts.append({
            "name": "Employment Tenure",
            "type": "negative",
            "effect": "Low Negative",
            "desc": f"Relatively new career tenure ({emp_days} days) shows transitional security."
        })

    # 4. Property Ownership
    prop = form.get("owns_property") or form.get("OwnsProperty")
    owns_property = prop in ["on", 1, "1", "true", True]
    if owns_property:
        impacts.append({
            "name": "Asset Holding",
            "type": "positive",
            "effect": "Moderate Positive",
            "desc": "Ownership of real estate property acts as a strong financial anchor."
        })

    # 5. Age Bracket Impact
    try:
        age = int(form.get("age") or form.get("Age") or 35)
    except (ValueError, TypeError):
        age = 35

    if age < 25:
        impacts.append({
            "name": "Age Profile",
            "type": "negative",
            "effect": "Low Negative",
            "desc": f"Younger applicant age ({age} years) correlates with shorter credit record span."
        })
    elif 30 <= age <= 60:
        impacts.append({
            "name": "Age Profile",
            "type": "positive",
            "effect": "Moderate Positive",
            "desc": f"Applicant age ({age} years) falls in the prime stability segment."
        })

    return impacts


# ─────────────────────────────────────────────
# Routes — Auth
# ─────────────────────────────────────────────
@app.route("/")
def index():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("login.html")

        user = query_db(
            "SELECT * FROM Users WHERE Email = %s", (email,), one=True
        )
        if user and check_password_hash(user["Password"], password):
            session.clear()
            session["user_id"] = user["UserID"]
            session["name"]    = user["Name"]
            session["email"]   = user["Email"]
            session["role"]    = user["Role"]
            flash(f"Welcome back, {user['Name']}!", "success")
            if user["Role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm_password", "")

        errors = []
        if not name:    errors.append("Full name is required.")
        if not email:   errors.append("Email is required.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != confirm:
            errors.append("Passwords do not match.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("register.html",
                                   name=name, email=email)

        existing = query_db(
            "SELECT UserID FROM Users WHERE Email = %s", (email,), one=True
        )
        if existing:
            flash("An account with that email already exists.", "danger")
            return render_template("register.html", name=name, email=email)

        query_db(
            "INSERT INTO Users (Name, Email, Password, Role) VALUES (%s,%s,%s,'user')",
            (name, email, generate_password_hash(password)),
            commit=True,
        )
        flash("Registration successful! Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


# ─────────────────────────────────────────────
# Routes — User Dashboard
# ─────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    uid = session["user_id"]
    total_apps = query_db(
        "SELECT COUNT(*) as c FROM Applicant_Details WHERE UserID=%s", (uid,), one=True
    )
    approved = query_db(
        """SELECT COUNT(*) as c FROM Approval_Prediction ap
           JOIN Applicant_Details ad ON ap.ApplicantID = ad.ApplicantID
           WHERE ad.UserID=%s AND ap.ApprovalResult='Approved'""",
        (uid,), one=True
    )
    rejected = query_db(
        """SELECT COUNT(*) as c FROM Approval_Prediction ap
           JOIN Applicant_Details ad ON ap.ApplicantID = ad.ApplicantID
           WHERE ad.UserID=%s AND ap.ApprovalResult='Rejected'""",
        (uid,), one=True
    )
    recent = query_db(
        """SELECT ad.FullName, ap.ApprovalResult, ap.RiskCategory,
                  ap.ConfidenceScore, ap.PredictionDate
           FROM Approval_Prediction ap
           JOIN Applicant_Details ad ON ap.ApplicantID = ad.ApplicantID
           WHERE ad.UserID=%s
           ORDER BY ap.PredictionDate DESC LIMIT 5""",
        (uid,)
    )
    stats = {
        "total":    total_apps["c"] if total_apps else 0,
        "approved": approved["c"]   if approved   else 0,
        "rejected": rejected["c"]   if rejected   else 0,
    }
    return render_template("dashboard.html", stats=stats, recent=recent)


# ─────────────────────────────────────────────
# Routes — Applicant Form
# ─────────────────────────────────────────────
@app.route("/apply", methods=["GET", "POST"])
@login_required
def apply():
    if request.method == "POST":
        uid = session["user_id"]
        form = request.form
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.accept_json

        # ── Server-side validation ──
        required = ["full_name", "age", "gender", "annual_income", "income_type",
                    "education_type", "family_status", "housing_type",
                    "employment_days", "family_member_count"]
        for field in required:
            if not form.get(field, "").strip():
                msg = f"Field '{field.replace('_',' ').title()}' is required."
                if is_ajax:
                    return jsonify({"success": False, "error": msg}), 400
                flash(msg, "danger")
                return render_template("applicant_form.html", form=form)

        try:
            age            = int(form["age"])
            annual_income  = float(form["annual_income"])
            emp_days       = int(form["employment_days"])
            family_count   = int(form["family_member_count"])
            num_children   = int(form.get("num_children", 0))
            months_balance = int(form.get("months_balance", -12))
            overdue_months = int(form.get("overdue_months", 0))
        except ValueError:
            msg = "Please enter valid numeric values."
            if is_ajax:
                return jsonify({"success": False, "error": msg}), 400
            flash(msg, "danger")
            return render_template("applicant_form.html", form=form)

        if not (18 <= age <= 80):
            msg = "Age must be between 18 and 80."
            if is_ajax:
                return jsonify({"success": False, "error": msg}), 400
            flash(msg, "danger")
            return render_template("applicant_form.html", form=form)
        if annual_income <= 0:
            msg = "Annual income must be positive."
            if is_ajax:
                return jsonify({"success": False, "error": msg}), 400
            flash(msg, "danger")
            return render_template("applicant_form.html", form=form)

        # ── Insert Applicant_Details ──
        applicant_id = query_db(
            """INSERT INTO Applicant_Details
               (UserID, FullName, Age, Gender, AnnualIncome, IncomeType, EducationType,
                FamilyStatus, HousingType, EmploymentDays, OwnsCar, OwnsProperty,
                NumChildren, FamilyMemberCount, WorkPhoneProvided, PhoneProvided, EmailProvided)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (uid, form["full_name"], age, form["gender"], annual_income,
             form["income_type"], form["education_type"], form["family_status"],
             form["housing_type"], emp_days,
             1 if form.get("owns_car") == "on" else 0,
             1 if form.get("owns_property") == "on" else 0,
             num_children, family_count,
             1 if form.get("work_phone_provided") == "on" else 0,
             1 if form.get("phone_provided") == "on" else 0,
             1 if form.get("email_provided") == "on" else 0),
            commit=True,
        )

        # ── Insert Credit_History ──
        payment_status = form.get("payment_status", "C")
        overdue_label  = ["No overdue","1-29 days overdue","30-59 days overdue",
                          "60-89 days overdue","90+ days overdue"]
        overdue_str    = overdue_label[min(overdue_months, 4)]
        query_db(
            """INSERT INTO Credit_History
               (ApplicantID, MonthsBalance, PaymentStatus, OverdueStatus)
               VALUES (%s,%s,%s,%s)""",
            (applicant_id, months_balance, payment_status, overdue_str),
            commit=True,
        )

        session["pending_applicant_id"] = applicant_id
        session["pending_form"] = dict(form)
        session["pending_form"]["overdue_months"] = overdue_months

        if is_ajax:
            return jsonify({"success": True, "applicant_id": applicant_id})

        return redirect(url_for("predict"))

    return render_template("applicant_form.html", form={})


# ─────────────────────────────────────────────
# Routes — Prediction
# ─────────────────────────────────────────────
@app.route("/predict", methods=["GET", "POST"])
@login_required
def predict():
    applicant_id = session.get("pending_applicant_id")
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest" or request.accept_mimetypes.accept_json
    if not applicant_id:
        if is_ajax:
            return jsonify({"success": False, "error": "Please complete the applicant form first."}), 400
        flash("Please complete the applicant form first.", "warning")
        return redirect(url_for("apply"))

    if request.method == "POST":
        pipeline = load_pipeline()
        if pipeline is None:
            if is_ajax:
                return jsonify({"success": False, "error": "ML model not found. Please run train_model.py first."}), 500
            flash("ML model not found. Please run train_model.py first.", "danger")
            return redirect(url_for("dashboard"))

        form_data = session.get("pending_form", {})
        model     = pipeline["model"]
        scaler    = pipeline["scaler"]

        X = build_feature_vector(form_data)

        # Scale the feature vector
        try:
            X_scaled = scaler.transform(X)
        except Exception:
            X_scaled = X   # fallback if shapes mismatch

        prob    = float(model.predict_proba(X_scaled)[0][1])
        label   = "Approved" if prob >= 0.50 else "Rejected"
        risk    = get_risk_category(prob)
        conf    = round(prob * 100, 2)

        # ── Get ModelID ──
        model_row = query_db(
            "SELECT ModelID FROM ML_Model WHERE IsBestModel=1 LIMIT 1", one=True
        )
        model_id = model_row["ModelID"] if model_row else 1

        # ── Insert Approval_Prediction ──
        pred_id = query_db(
            """INSERT INTO Approval_Prediction
               (ApplicantID, ModelID, ApprovalResult, RiskCategory, ConfidenceScore)
               VALUES (%s,%s,%s,%s,%s)""",
            (applicant_id, model_id, label, risk, conf),
            commit=True,
        )

        # ── Get Model Metadata for AJAX ──
        model_meta = query_db("SELECT ModelName, AlgorithmType FROM ML_Model WHERE ModelID = %s", (model_id,), one=True)
        model_name = model_meta["ModelName"] if model_meta else "Best Deployed Model"
        algorithm_type = model_meta["AlgorithmType"] if model_meta else "ML Algorithm"

        # Calculate impacts for AJAX
        impacts = calculate_feature_impacts(form_data, prob)

        # ── Clear session temp keys ──
        session.pop("pending_applicant_id", None)
        session.pop("pending_form", None)

        if is_ajax:
            return jsonify({
                "success": True,
                "prediction_id": pred_id,
                "applicant_id": applicant_id,
                "result": label,
                "risk": risk,
                "confidence": conf,
                "model_name": model_name,
                "algorithm_type": algorithm_type.replace('_',' ').title(),
                "name": form_data.get("full_name"),
                "age": form_data.get("age"),
                "income": form_data.get("annual_income"),
                "income_type": form_data.get("income_type"),
                "education_type": form_data.get("education_type"),
                "family_status": form_data.get("family_status"),
                "housing_type": form_data.get("housing_type"),
                "impacts": impacts
            })

        return redirect(url_for("result", pred_id=pred_id))

    return render_template("predict.html")


# ─────────────────────────────────────────────
# Routes — Result
# ─────────────────────────────────────────────
@app.route("/result/<int:pred_id>")
@login_required
def result(pred_id):
    row = query_db(
        """SELECT ap.*, ad.FullName, ad.Age, ad.AnnualIncome,
                  ad.IncomeType, ad.EducationType, ad.FamilyStatus,
                  ad.HousingType, ad.EmploymentDays, ad.OwnsCar, ad.OwnsProperty,
                  ad.NumChildren, ad.FamilyMemberCount,
                  ch.MonthsBalance, ch.PaymentStatus, ch.OverdueStatus,
                  m.ModelName, m.AlgorithmType, m.Accuracy
           FROM Approval_Prediction ap
           JOIN Applicant_Details ad ON ap.ApplicantID = ad.ApplicantID
           JOIN ML_Model m           ON ap.ModelID     = m.ModelID
           JOIN Users u              ON ad.UserID       = u.UserID
           LEFT JOIN Credit_History ch ON ad.ApplicantID = ch.ApplicantID
           WHERE ap.PredictionID = %s AND u.UserID = %s""",
        (pred_id, session["user_id"]), one=True,
    )
    if not row:
        abort(404)
    
    # Calculate feature impacts for the results template
    prob = float(row["ConfidenceScore"]) / 100.0
    impacts = calculate_feature_impacts(row, prob)
    return render_template("result.html", pred=row, impacts=impacts)


# ─────────────────────────────────────────────
# Routes — History
# ─────────────────────────────────────────────
@app.route("/history")
@login_required
def history():
    uid  = session["user_id"]
    page = max(1, int(request.args.get("page", 1)))
    per  = 10
    off  = (page - 1) * per

    rows = query_db(
        """SELECT ap.PredictionID, ad.FullName, ap.ApprovalResult,
                  ap.RiskCategory, ap.ConfidenceScore, ap.PredictionDate,
                  m.ModelName
           FROM Approval_Prediction ap
           JOIN Applicant_Details ad ON ap.ApplicantID = ad.ApplicantID
           JOIN ML_Model m           ON ap.ModelID     = m.ModelID
           WHERE ad.UserID = %s
           ORDER BY ap.PredictionDate DESC
           LIMIT %s OFFSET %s""",
        (uid, per, off)
    )
    total = query_db(
        """SELECT COUNT(*) as c FROM Approval_Prediction ap
           JOIN Applicant_Details ad ON ap.ApplicantID = ad.ApplicantID
           WHERE ad.UserID = %s""",
        (uid,), one=True
    )
    total_pages = max(1, ((total["c"] if total else 0) + per - 1) // per)
    return render_template("history.html", rows=rows,
                           page=page, total_pages=total_pages)


# ─────────────────────────────────────────────
# Routes — Model Info
# ─────────────────────────────────────────────
@app.route("/models")
@login_required
def model_info():
    models = query_db(
        "SELECT * FROM ML_Model ORDER BY ROC_AUC DESC"
    )
    return render_template("model_info.html", models=models)


# ─────────────────────────────────────────────
# Routes — Admin Dashboard
# ─────────────────────────────────────────────
@app.route("/admin")
@admin_required
def admin_dashboard():
    stats = {
        "total_users":       query_db("SELECT COUNT(*) as c FROM Users WHERE Role='user'", one=True)["c"],
        "total_applicants":  query_db("SELECT COUNT(*) as c FROM Applicant_Details", one=True)["c"],
        "total_predictions": query_db("SELECT COUNT(*) as c FROM Approval_Prediction", one=True)["c"],
        "total_approved":    query_db("SELECT COUNT(*) as c FROM Approval_Prediction WHERE ApprovalResult='Approved'", one=True)["c"],
        "total_rejected":    query_db("SELECT COUNT(*) as c FROM Approval_Prediction WHERE ApprovalResult='Rejected'", one=True)["c"],
        "total_models":      query_db("SELECT COUNT(*) as c FROM ML_Model", one=True)["c"],
    }
    recent_preds = query_db(
        """SELECT ap.PredictionID, ad.FullName, u.Email, ap.ApprovalResult,
                  ap.RiskCategory, ap.ConfidenceScore, ap.PredictionDate
           FROM Approval_Prediction ap
           JOIN Applicant_Details ad ON ap.ApplicantID = ad.ApplicantID
           JOIN Users u              ON ad.UserID       = u.UserID
           ORDER BY ap.PredictionDate DESC LIMIT 10"""
    )
    return render_template("admin/dashboard.html", stats=stats, recent_preds=recent_preds)


@app.route("/admin/users")
@admin_required
def admin_users():
    q    = request.args.get("q", "").strip()
    page = max(1, int(request.args.get("page", 1)))
    per  = 15
    off  = (page - 1) * per

    if q:
        users = query_db(
            "SELECT * FROM Users WHERE Name LIKE %s OR Email LIKE %s "
            "ORDER BY CreatedAt DESC LIMIT %s OFFSET %s",
            (f"%{q}%", f"%{q}%", per, off)
        )
        total = query_db(
            "SELECT COUNT(*) as c FROM Users WHERE Name LIKE %s OR Email LIKE %s",
            (f"%{q}%", f"%{q}%"), one=True
        )
    else:
        users = query_db(
            "SELECT * FROM Users ORDER BY CreatedAt DESC LIMIT %s OFFSET %s",
            (per, off)
        )
        total = query_db("SELECT COUNT(*) as c FROM Users", one=True)

    total_pages = max(1, ((total["c"] if total else 0) + per - 1) // per)
    return render_template("admin/users.html", users=users, q=q,
                           page=page, total_pages=total_pages)


@app.route("/admin/users/delete/<int:uid>", methods=["POST"])
@admin_required
def admin_delete_user(uid):
    if uid == session["user_id"]:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("admin_users"))
    query_db("DELETE FROM Users WHERE UserID=%s", (uid,), commit=True)
    flash("User deleted successfully.", "success")
    return redirect(url_for("admin_users"))


@app.route("/admin/applicants")
@admin_required
def admin_applicants():
    q    = request.args.get("q", "").strip()
    page = max(1, int(request.args.get("page", 1)))
    per  = 15
    off  = (page - 1) * per

    base_sql = """
        SELECT ad.*, u.Name as UserName, u.Email as UserEmail
        FROM Applicant_Details ad
        JOIN Users u ON ad.UserID = u.UserID
    """
    if q:
        rows = query_db(
            base_sql + " WHERE ad.FullName LIKE %s OR u.Email LIKE %s "
            "ORDER BY ad.SubmittedAt DESC LIMIT %s OFFSET %s",
            (f"%{q}%", f"%{q}%", per, off)
        )
        total = query_db(
            "SELECT COUNT(*) as c FROM Applicant_Details ad JOIN Users u ON ad.UserID=u.UserID "
            "WHERE ad.FullName LIKE %s OR u.Email LIKE %s",
            (f"%{q}%", f"%{q}%"), one=True
        )
    else:
        rows = query_db(
            base_sql + " ORDER BY ad.SubmittedAt DESC LIMIT %s OFFSET %s", (per, off)
        )
        total = query_db("SELECT COUNT(*) as c FROM Applicant_Details", one=True)

    total_pages = max(1, ((total["c"] if total else 0) + per - 1) // per)
    return render_template("admin/applicants.html", rows=rows, q=q,
                           page=page, total_pages=total_pages)


@app.route("/admin/applicants/delete/<int:aid>", methods=["POST"])
@admin_required
def admin_delete_applicant(aid):
    query_db("DELETE FROM Applicant_Details WHERE ApplicantID=%s", (aid,), commit=True)
    flash("Applicant record deleted.", "success")
    return redirect(url_for("admin_applicants"))


@app.route("/admin/predictions")
@admin_required
def admin_predictions():
    q    = request.args.get("q", "").strip()
    page = max(1, int(request.args.get("page", 1)))
    per  = 15
    off  = (page - 1) * per

    base_sql = """
        SELECT ap.PredictionID, ad.FullName, u.Email,
               ap.ApprovalResult, ap.RiskCategory,
               ap.ConfidenceScore, ap.PredictionDate, m.ModelName
        FROM Approval_Prediction ap
        JOIN Applicant_Details ad ON ap.ApplicantID = ad.ApplicantID
        JOIN Users u              ON ad.UserID       = u.UserID
        JOIN ML_Model m           ON ap.ModelID      = m.ModelID
    """
    if q:
        rows = query_db(
            base_sql + " WHERE ad.FullName LIKE %s OR ap.ApprovalResult LIKE %s "
            "ORDER BY ap.PredictionDate DESC LIMIT %s OFFSET %s",
            (f"%{q}%", f"%{q}%", per, off)
        )
        total = query_db(
            """SELECT COUNT(*) as c FROM Approval_Prediction ap
               JOIN Applicant_Details ad ON ap.ApplicantID=ad.ApplicantID
               WHERE ad.FullName LIKE %s OR ap.ApprovalResult LIKE %s""",
            (f"%{q}%", f"%{q}%"), one=True
        )
    else:
        rows = query_db(
            base_sql + " ORDER BY ap.PredictionDate DESC LIMIT %s OFFSET %s", (per, off)
        )
        total = query_db("SELECT COUNT(*) as c FROM Approval_Prediction", one=True)

    total_pages = max(1, ((total["c"] if total else 0) + per - 1) // per)
    return render_template("admin/predictions.html", rows=rows, q=q,
                           page=page, total_pages=total_pages)


@app.route("/admin/predictions/delete/<int:pid>", methods=["POST"])
@admin_required
def admin_delete_prediction(pid):
    query_db("DELETE FROM Approval_Prediction WHERE PredictionID=%s", (pid,), commit=True)
    flash("Prediction record deleted.", "success")
    return redirect(url_for("admin_predictions"))


@app.route("/admin/export/predictions")
@admin_required
def export_predictions_csv():
    rows = query_db(
        """SELECT ap.PredictionID, ad.FullName, u.Email, ad.Age,
                  ad.AnnualIncome, ad.IncomeType, ad.EducationType,
                  ad.FamilyStatus, ad.HousingType, ad.EmploymentDays,
                  ap.ApprovalResult, ap.RiskCategory, ap.ConfidenceScore,
                  ap.PredictionDate, m.ModelName
           FROM Approval_Prediction ap
           JOIN Applicant_Details ad ON ap.ApplicantID = ad.ApplicantID
           JOIN Users u              ON ad.UserID       = u.UserID
           JOIN ML_Model m           ON ap.ModelID      = m.ModelID
           ORDER BY ap.PredictionDate DESC"""
    )
    si = io.StringIO()
    writer = csv.DictWriter(si, fieldnames=[
        "PredictionID","FullName","Email","Age","AnnualIncome","IncomeType",
        "EducationType","FamilyStatus","HousingType","EmploymentDays",
        "ApprovalResult","RiskCategory","ConfidenceScore","PredictionDate","ModelName"
    ])
    writer.writeheader()
    for row in (rows or []):
        writer.writerow({k: row.get(k, "") for k in writer.fieldnames})

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=predictions_export.csv"}
    )


@app.route("/admin/export/users")
@admin_required
def export_users_csv():
    rows = query_db("SELECT UserID, Name, Email, Role, CreatedAt FROM Users ORDER BY CreatedAt")
    si = io.StringIO()
    writer = csv.DictWriter(si, fieldnames=["UserID","Name","Email","Role","CreatedAt"])
    writer.writeheader()
    for row in (rows or []):
        writer.writerow({k: row.get(k, "") for k in writer.fieldnames})
    return Response(
        si.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=users_export.csv"}
    )


# ─────────────────────────────────────────────
# API — chart data for dashboard
# ─────────────────────────────────────────────
@app.route("/api/chart/monthly")
@login_required
def api_monthly_chart():
    uid  = session["user_id"]
    role = session.get("role")
    if role == "admin":
        rows = query_db(
            """SELECT DATE_FORMAT(PredictionDate,'%Y-%m') as month,
                      SUM(ApprovalResult='Approved') as approved,
                      SUM(ApprovalResult='Rejected') as rejected
               FROM Approval_Prediction
               GROUP BY month ORDER BY month DESC LIMIT 6"""
        )
    else:
        rows = query_db(
            """SELECT DATE_FORMAT(ap.PredictionDate,'%Y-%m') as month,
                      SUM(ap.ApprovalResult='Approved') as approved,
                      SUM(ap.ApprovalResult='Rejected') as rejected
               FROM Approval_Prediction ap
               JOIN Applicant_Details ad ON ap.ApplicantID=ad.ApplicantID
               WHERE ad.UserID=%s
               GROUP BY month ORDER BY month DESC LIMIT 6""",
            (uid,)
        )
    return jsonify(rows or [])


# ─────────────────────────────────────────────
# Routes — Credit Sandbox
# ─────────────────────────────────────────────
@app.route("/sandbox")
@login_required
def sandbox():
    return render_template("sandbox.html")


@app.route("/api/predict/sandbox", methods=["POST"])
@login_required
def api_predict_sandbox():
    pipeline = load_pipeline()
    if pipeline is None:
        return jsonify({"success": False, "error": "ML model not found."}), 500

    form = request.json or {}
    model = pipeline["model"]
    scaler = pipeline["scaler"]

    # Reconstruct the feature vector.
    X = build_feature_vector(form)

    # Scale the feature vector
    try:
        X_scaled = scaler.transform(X)
    except Exception:
        X_scaled = X

    prob = float(model.predict_proba(X_scaled)[0][1])
    label = "Approved" if prob >= 0.50 else "Rejected"
    risk = get_risk_category(prob)
    conf = round(prob * 100, 2)

    # Calculate Feature Impacts (XAI)
    impacts = calculate_feature_impacts(form, prob)

    # Get model metadata
    model_row = query_db(
        "SELECT ModelName, AlgorithmType FROM ML_Model WHERE IsBestModel=1 LIMIT 1", one=True
    )
    model_name = model_row["ModelName"] if model_row else "Best Deployed Model"
    algorithm_type = model_row["AlgorithmType"] if model_row else "ML Algorithm"

    return jsonify({
        "success": True,
        "result": label,
        "risk": risk,
        "confidence": conf,
        "impacts": impacts,
        "model_name": model_name,
        "algorithm_type": algorithm_type.replace('_',' ').title()
    })


# ─────────────────────────────────────────────
# Error handlers
# ─────────────────────────────────────────────
@app.errorhandler(403)
def forbidden(e):
    return render_template("errors/403.html"), 403


@app.errorhandler(404)
def not_found(e):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("errors/500.html"), 500


# ─────────────────────────────────────────────
# Context processor — inject current hour into every template
# ─────────────────────────────────────────────
@app.context_processor
def inject_globals():
    return {"now_hour": datetime.now().hour}


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────
if __name__ == "__main__":
    with app.app_context():
        seed_database()
    app.run(debug=Config.DEBUG, host="0.0.0.0", port=5000)
