"""
train_model.py
==============
Credit Card Approval Prediction – Full ML Training Pipeline

Steps:
  1. Generate synthetic credit application dataset
  2. Data cleaning & missing value handling
  3. Feature engineering
  4. Label encoding
  5. Train-test split
  6. Train four models: Logistic Regression, Decision Tree, Random Forest, XGBoost
  7. Evaluate all models (Accuracy, Precision, Recall, F1, ROC AUC)
  8. Save the best model as models/model.pkl
  9. Save all individual models
  10. Print comparison table & update DB with metrics
"""

import os
import sys
import json
import warnings
import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, roc_auc_score, classification_report, confusion_matrix
)
from xgboost import XGBClassifier

warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# Paths
# ─────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

RANDOM_STATE = 42
np.random.seed(RANDOM_STATE)


# ─────────────────────────────────────────────
# 1. Generate Synthetic Dataset
# ─────────────────────────────────────────────
def generate_dataset(n_samples: int = 5000) -> pd.DataFrame:
    """
    Generate a realistic synthetic credit-card application dataset.
    Features mirror the UCI Credit Card / Kaggle credit dataset structure.
    """
    rng = np.random.default_rng(RANDOM_STATE)

    income_types   = ["Working", "Commercial associate", "Pensioner", "State servant", "Student"]
    edu_types      = ["Higher education", "Secondary / secondary special",
                      "Incomplete higher", "Lower secondary", "Academic degree"]
    family_status  = ["Married", "Single / not married", "Civil marriage", "Separated", "Widow"]
    housing_types  = ["House / apartment", "With parents", "Municipal apartment",
                      "Rented apartment", "Office apartment", "Co-op apartment"]

    data = {
        "Gender":              rng.choice(["M", "F"], n_samples, p=[0.42, 0.58]),
        "OwnsCar":             rng.integers(0, 2, n_samples),
        "OwnsProperty":        rng.integers(0, 2, n_samples, endpoint=False),
        "NumChildren":         rng.integers(0, 6, n_samples),
        "AnnualIncome":        rng.integers(60000, 1500000, n_samples).astype(float),
        "IncomeType":          rng.choice(income_types,  n_samples, p=[0.52, 0.23, 0.15, 0.08, 0.02]),
        "EducationType":       rng.choice(edu_types,     n_samples, p=[0.30, 0.49, 0.10, 0.08, 0.03]),
        "FamilyStatus":        rng.choice(family_status, n_samples, p=[0.64, 0.15, 0.05, 0.06, 0.10]),
        "HousingType":         rng.choice(housing_types, n_samples, p=[0.72, 0.09, 0.07, 0.05, 0.02, 0.05]),
        "Age":                 rng.integers(21, 70, n_samples),
        "EmploymentDays":      rng.integers(-365*15, 365*20, n_samples),
        "WorkPhoneProvided":   rng.integers(0, 2, n_samples),
        "PhoneProvided":       rng.integers(0, 2, n_samples),
        "EmailProvided":       rng.integers(0, 2, n_samples),
        "FamilyMemberCount":   rng.integers(1, 8, n_samples),
        "MonthsBalance":       rng.integers(-60, 0, n_samples),
        "OverdueMonths":       rng.choice([0, 1, 2, 3], n_samples, p=[0.70, 0.15, 0.10, 0.05]),
    }

    df = pd.DataFrame(data)

    # ── Feature engineering within generation ──
    df["IsEmployed"]    = (df["EmploymentDays"] > 0).astype(int)
    df["IncomePerMember"] = df["AnnualIncome"] / df["FamilyMemberCount"].clip(lower=1)

    # ── Synthetic target: 1 = Approved, 0 = Rejected ──
    # Higher income, employed, educated, married → more likely approved
    score = (
          (df["AnnualIncome"] > 300000).astype(int) * 2
        + (df["EducationType"] == "Higher education").astype(int) * 2
        + (df["EducationType"] == "Academic degree").astype(int) * 3
        + (df["IsEmployed"] == 1).astype(int) * 2
        + (df["FamilyStatus"] == "Married").astype(int)
        + df["OwnsProperty"]
        + df["OwnsCar"]
        - df["NumChildren"]
        - df["OverdueMonths"] * 2
        + (df["IncomeType"] == "State servant").astype(int)
        + rng.normal(0, 1.5, n_samples)
    )
    df["TARGET"] = (score >= 4).astype(int)

    return df


# ─────────────────────────────────────────────
# 2. Preprocessing
# ─────────────────────────────────────────────
def preprocess(df: pd.DataFrame):
    """
    Clean, encode, and engineer features. Returns X, y, encoders dict, scaler.
    """
    df = df.copy()

    # ── Missing value handling ──
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].fillna(df[col].mode()[0])
    for col in df.select_dtypes(include="number").columns:
        df[col] = df[col].fillna(df[col].median())

    # ── Feature engineering ──
    df["AgeBin"]           = pd.cut(df["Age"], bins=[20,30,40,50,60,70],
                                     labels=["21-30","31-40","41-50","51-60","61-70"])
    df["IncomeBin"]        = pd.qcut(df["AnnualIncome"], q=4,
                                      labels=["Low","Medium","High","Very High"])
    df["EmploymentYears"]  = (df["EmploymentDays"].abs() / 365).round(1)
    df["HighRiskOverdue"]  = (df["OverdueMonths"] >= 2).astype(int)

    # ── Label encoding for categorical columns ──
    cat_cols = df.select_dtypes(include=["object", "category"]).columns.tolist()
    encoders = {}
    for col in cat_cols:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col].astype(str))
        encoders[col] = le

    # ── Separate features and target ──
    y = df["TARGET"]
    X = df.drop(columns=["TARGET"])

    # ── Scale numeric features ──
    scaler = StandardScaler()
    X_scaled = pd.DataFrame(scaler.fit_transform(X), columns=X.columns)

    return X_scaled, y, encoders, scaler, X.columns.tolist()


# ─────────────────────────────────────────────
# 3. Train Models
# ─────────────────────────────────────────────
def build_models() -> dict:
    return {
        "Logistic Regression": LogisticRegression(
            max_iter=1000, random_state=RANDOM_STATE, class_weight="balanced"
        ),
        "Decision Tree": DecisionTreeClassifier(
            max_depth=8, min_samples_split=20, random_state=RANDOM_STATE,
            class_weight="balanced"
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=200, max_depth=10, min_samples_split=15,
            random_state=RANDOM_STATE, class_weight="balanced", n_jobs=-1
        ),
        "XGBoost": XGBClassifier(
            n_estimators=200, max_depth=6, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8,
            random_state=RANDOM_STATE, eval_metric="logloss",
            use_label_encoder=False, n_jobs=-1
        ),
    }


def evaluate_model(model, X_test, y_test) -> dict:
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    return {
        "accuracy":  round(accuracy_score(y_test, y_pred),   4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall":    round(recall_score(y_test, y_pred,    zero_division=0), 4),
        "f1":        round(f1_score(y_test, y_pred,        zero_division=0), 4),
        "roc_auc":   round(roc_auc_score(y_test, y_prob),  4),
    }


# ─────────────────────────────────────────────
# 4. Main Pipeline
# ─────────────────────────────────────────────
def main():
    print("=" * 65)
    print("  Credit Card Approval Prediction - ML Training Pipeline")
    print("=" * 65)

    # Step 1 – Generate data
    print("\n[1/6] Generating synthetic dataset (5,000 samples)...")
    df = generate_dataset(5000)
    print(f"      Shape: {df.shape}  |  Approval rate: {df['TARGET'].mean():.1%}")

    # Step 2 – Preprocess
    print("[2/6] Preprocessing (clean, encode, engineer features)...")
    X, y, encoders, scaler, feature_names = preprocess(df)
    print(f"      Features: {len(feature_names)}")

    # Step 3 – Train/test split
    print("[3/6] Splitting: 80% train / 20% test (stratified)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=RANDOM_STATE, stratify=y
    )

    # Step 4 – Train & evaluate
    print("[4/6] Training and evaluating 4 models...\n")
    models     = build_models()
    results    = {}
    trained    = {}
    header     = f"{'Model':<25} {'Acc':>7} {'Prec':>7} {'Recall':>7} {'F1':>7} {'AUC':>7}"
    divider    = "-" * 65
    print(header)
    print(divider)

    for name, model in models.items():
        model.fit(X_train, y_train)
        metrics = evaluate_model(model, X_test, y_test)
        results[name] = metrics
        trained[name] = model
        print(f"  {name:<23} {metrics['accuracy']:>7.4f} {metrics['precision']:>7.4f} "
              f"{metrics['recall']:>7.4f} {metrics['f1']:>7.4f} {metrics['roc_auc']:>7.4f}")

    # Step 5 – Pick best model by ROC AUC
    print(divider)
    best_name = max(results, key=lambda n: results[n]["roc_auc"])
    best_model = trained[best_name]
    print(f"\n[5/6] Best model: {best_name}  (ROC AUC = {results[best_name]['roc_auc']:.4f})")

    # Step 6 – Save artefacts
    print("[6/6] Saving model artefacts...")
    algo_map = {
        "Logistic Regression": "logistic_regression",
        "Decision Tree":       "decision_tree",
        "Random Forest":       "random_forest",
        "XGBoost":             "xgboost",
    }
    saved_paths = {}
    for name, model in trained.items():
        fname = f"{algo_map[name]}.pkl"
        path  = os.path.join(MODELS_DIR, fname)
        joblib.dump(model, path)
        saved_paths[name] = path
        print(f"      Saved: models/{fname}")

    # Save pipeline (best model + scaler + encoders + feature names)
    pipeline = {
        "model":         best_model,
        "scaler":        scaler,
        "encoders":      encoders,
        "feature_names": feature_names,
        "best_model_name": best_name,
    }
    pipeline_path = os.path.join(MODELS_DIR, "model.pkl")
    joblib.dump(pipeline, pipeline_path)
    print(f"      Saved: models/model.pkl  <- BEST MODEL PIPELINE")

    # Save metrics JSON (read by app.py to seed DB)
    metrics_payload = []
    for name, metrics in results.items():
        metrics_payload.append({
            "model_name":     name,
            "algorithm_type": algo_map[name],
            "accuracy":       metrics["accuracy"],
            "precision":      metrics["precision"],
            "recall":         metrics["recall"],
            "f1":             metrics["f1"],
            "roc_auc":        metrics["roc_auc"],
            "model_file":     f"models/{algo_map[name]}.pkl",
            "is_best":        name == best_name,
        })
    metrics_path = os.path.join(MODELS_DIR, "metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics_payload, f, indent=2)
    print(f"      Saved: models/metrics.json")

    # Final classification report for best model
    y_pred_best = best_model.predict(X_test)
    print(f"\n{'=' * 65}")
    print(f"  Classification Report - {best_name}")
    print(f"{'=' * 65}")
    print(classification_report(y_test, y_pred_best, target_names=["Rejected", "Approved"]))

    cm = confusion_matrix(y_test, y_pred_best)
    print("  Confusion Matrix:")
    print(f"    TN={cm[0,0]}  FP={cm[0,1]}")
    print(f"    FN={cm[1,0]}  TP={cm[1,1]}")
    print(f"\n  Training complete. All artefacts saved to: {MODELS_DIR}")
    print("=" * 65)

    return results, best_name


if __name__ == "__main__":
    main()
