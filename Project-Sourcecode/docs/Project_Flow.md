# Project Flow
## Credit Card Approval Prediction System

---

## End-to-End User Journey

```
┌─────────────────────────────────────────────────┐
│                   USER JOURNEY                   │
└─────────────────────────────────────────────────┘

  Visit http://localhost:5000
              │
              ▼
  ┌─────────────────────┐
  │   Login / Register  │  ← New users register, existing users log in
  └──────────┬──────────┘
             │
             ├─── Admin Role ──────────────────────────────────┐
             │                                                  │
             ▼                                                  ▼
  ┌─────────────────────┐                          ┌──────────────────────┐
  │   User Dashboard    │                          │   Admin Dashboard    │
  │  • Stats cards      │                          │  • System overview   │
  │  • Charts           │                          │  • All stats         │
  │  • Recent preds     │                          │  • Manage users      │
  │  • Quick actions    │                          │  • Manage applicants │
  └──────────┬──────────┘                          │  • All predictions   │
             │                                     │  • Export CSV        │
             ▼                                     └──────────────────────┘
  ┌─────────────────────┐
  │  Applicant Form     │  ← Multi-step, 3 sections
  │  Step 1: Personal   │     Name, Age, Gender, Housing, Family
  │  Step 2: Financial  │     Income, Income Type, Education, Employment
  │  Step 3: Credit     │     Payment History, Overdue Months
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │  Server Validation  │  ← Flask validates all required fields
  │  • Required fields  │     Type checking, range validation
  │  • Type checks      │
  │  • Range validation │
  └──────────┬──────────┘
             │ Pass
             ▼
  ┌─────────────────────┐
  │  DB: INSERT          │  ← Stores Applicant_Details + Credit_History
  │  Applicant_Details  │
  │  Credit_History     │
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │  Prediction Page    │  ← Animated AI processing screen
  │  • AI ring anim.    │     5 processing steps shown
  │  • Progress bar     │     Auto-submits after 3.8 seconds
  │  • Step checklist   │
  └──────────┬──────────┘
             │  POST /predict
             ▼
  ┌─────────────────────┐
  │  ML Inference       │
  │  1. Load model.pkl  │
  │  2. Build features  │
  │  3. Scale features  │
  │  4. predict_proba() │
  │  5. Threshold ≥0.50 │
  │  6. Risk category   │
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │  DB: INSERT          │  ← Stores result to Approval_Prediction
  │  Approval_Prediction│
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │   Result Page       │  ← Shows final decision
  │  • Approved/Rejected│     Confidence gauge, detail grid
  │  • Risk category    │     Recommendation message
  │  • Confidence gauge │     Print / New application options
  │  • Recommendation   │
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │  Prediction History │  ← Paginated table of all past predictions
  └─────────────────────┘
```

---

## ML Training Flow (train_model.py)

```
  python train_model.py
         │
         ▼
  ┌─────────────────────┐
  │  Generate Dataset   │  5,000 synthetic samples with realistic distributions
  │  (n=5000)           │  Features: 17 raw + engineered
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │  Data Cleaning      │  Fill missing: mode for categorical, median for numeric
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │  Feature Engineering│  AgeBin, IncomeBin, EmploymentYears,
  │                     │  IsEmployed, IncomePerMember, HighRiskOverdue
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │  Label Encoding     │  LabelEncoder for all categorical columns
  │  Standard Scaling   │  StandardScaler for all numeric features
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │  Train-Test Split   │  80% train / 20% test, stratified by TARGET
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────────────────────────────┐
  │              Train 4 Models                  │
  │  ┌──────────┐ ┌──────────┐ ┌────────────┐  │
  │  │Logistic  │ │Decision  │ │Random      │  │
  │  │Regression│ │Tree      │ │Forest      │  │
  │  └──────────┘ └──────────┘ └────────────┘  │
  │              ┌──────────┐                   │
  │              │ XGBoost  │                   │
  │              └──────────┘                   │
  └──────────┬──────────────────────────────────┘
             │
             ▼
  ┌─────────────────────┐
  │  Evaluate All       │  Accuracy, Precision, Recall, F1, ROC AUC
  │  Print Comparison   │  for each model on held-out test set
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │  Select Best Model  │  argmax(ROC AUC)
  └──────────┬──────────┘
             │
             ▼
  ┌─────────────────────┐
  │  Save Artefacts     │  models/logistic_regression.pkl
  │                     │  models/decision_tree.pkl
  │                     │  models/random_forest.pkl
  │                     │  models/xgboost.pkl
  │                     │  models/model.pkl  ← Best pipeline
  │                     │  models/metrics.json
  └─────────────────────┘
```

---

## Admin Workflow

```
Admin Login
    │
    ▼
Admin Dashboard ──── View system stats, recent predictions, charts
    │
    ├── Manage Users ──── Search · View · Delete (with cascade)
    │
    ├── Manage Applicants ── Search · View details · Delete
    │
    ├── Manage Predictions ── Search · Filter · Delete · View result
    │
    ├── Export Predictions CSV ── Full data export
    │
    └── Export Users CSV ── User list export
```
