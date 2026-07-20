# Technical Architecture
## Credit Card Approval Prediction System

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT BROWSER                          │
│  Bootstrap 5 · CSS Glassmorphism · Chart.js · Vanilla JS       │
└────────────────────────────┬───────────────────────────────────┘
                             │ HTTP/HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FLASK APPLICATION                          │
│                                                                  │
│  ┌────────────────┐  ┌──────────────────┐  ┌────────────────┐  │
│  │  Auth Layer    │  │   Route Layer    │  │  API Layer     │  │
│  │  login_required│  │  /dashboard      │  │  /api/chart/   │  │
│  │  admin_required│  │  /apply          │  │   monthly      │  │
│  │  session mgmt  │  │  /predict        │  │                │  │
│  └────────────────┘  │  /result         │  └────────────────┘  │
│                       │  /history        │                       │
│  ┌────────────────┐  │  /models         │  ┌────────────────┐  │
│  │  ML Inference  │  │  /admin/*        │  │  CSV Export    │  │
│  │  load_pipeline │  └──────────────────┘  │  /admin/export/│  │
│  │  predict_proba │                         └────────────────┘  │
│  │  risk_category │  ┌──────────────────┐                       │
│  └────────────────┘  │  DB Helper Layer │                       │
│                       │  query_db()      │                       │
│                       │  get_db()        │                       │
│                       └────────┬─────────┘                       │
└────────────────────────────────┼───────────────────────────────┘
                                 │
            ┌────────────────────┼──────────────────────┐
            ▼                    ▼                       ▼
  ┌──────────────────┐  ┌──────────────────┐  ┌─────────────────┐
  │   MySQL 8.0      │  │   ML Models      │  │   File System   │
  │                  │  │   (Joblib pkl)   │  │                 │
  │  Users           │  │                  │  │  models/        │
  │  Applicant_Details│  │  model.pkl       │  │  exports/       │
  │  Credit_History  │  │  (pipeline:      │  │  static/        │
  │  ML_Model        │  │   model+scaler   │  │  templates/     │
  │  Approval_Pred.  │  │   +encoders)     │  │                 │
  └──────────────────┘  └──────────────────┘  └─────────────────┘
```

---

## Layer Descriptions

### 1. Presentation Layer (Frontend)
- **HTML5** templates rendered by Jinja2 (server-side)
- **CSS3** with custom glassmorphism design system (no Bootstrap overrides)
- **Bootstrap 5.3** for grid layout and utility classes only
- **Chart.js 4.4** for bar, donut, and radar charts
- **Bootstrap Icons** for all iconography
- **Vanilla JavaScript** for: page loader, sidebar, live clock, counter animation, form validation, API calls

### 2. Application Layer (Flask)
- **Flask 3.0** WSGI application
- **Routing** — 20+ routes covering auth, user flows, admin CRUD, CSV export, and API
- **Session Management** — Server-side Flask sessions with `SECRET_KEY`
- **Auth Decorators** — `@login_required`, `@admin_required` using `functools.wraps`
- **Context Processor** — Injects `now_hour` globally for greeting messages
- **Error Handlers** — Custom 403, 404, 500 pages

### 3. Business Logic Layer
- **Prediction Pipeline**
  1. Form data → `build_feature_vector()` → 23-feature NumPy array
  2. `scaler.transform()` → StandardScaler normalisation
  3. `model.predict_proba()` → approval probability [0,1]
  4. Threshold 0.50 → 'Approved' / 'Rejected'
  5. `get_risk_category()` → 'Low' / 'Medium' / 'High' risk
  6. Store to `Approval_Prediction` table
- **Seed on Startup** — Admin user + ML model records auto-created on first run

### 4. Data Access Layer
- **`query_db(sql, args, one, commit)`** — Generic parameterised query executor
- **`get_db()`** — New `mysql.connector` connection per request (connection pooling not needed at this scale)
- All queries use `%s` placeholders — **no string formatting**, preventing SQL injection

### 5. ML Layer (Offline Training)
- **`train_model.py`** — Standalone script, not imported by Flask
- **Pipeline Object** — `{ model, scaler, encoders, feature_names, best_model_name }`
- **Model Selection** — Best by `roc_auc_score` on 20% held-out test set
- **4 Models** trained in a single loop, evaluated, pickled individually + best pipeline saved

### 6. Database Layer (MySQL 8.0)
- **5 normalised tables** with FK constraints and proper indexes
- **InnoDB engine** — ACID compliance, FK support
- **utf8mb4 charset** — Full Unicode support
- **Cascade deletes** — Deleting a user cascades to applicants → predictions

---

## Request-Response Cycle (Prediction Flow)

```
Browser                Flask                  MySQL               ML Engine
  │                      │                       │                     │
  │─── POST /apply ─────►│                       │                     │
  │                      │─── INSERT Applicant ─►│                     │
  │                      │─── INSERT History ───►│                     │
  │                      │◄── applicant_id ──────│                     │
  │◄── redirect /predict │                       │                     │
  │                      │                       │                     │
  │─── POST /predict ───►│                       │                     │
  │                      │─── load model.pkl ──────────────────────────►│
  │                      │◄── pipeline ─────────────────────────────────│
  │                      │─── build_feature_vector()                    │
  │                      │─── scaler.transform()                        │
  │                      │─── model.predict_proba() ────────────────────►│
  │                      │◄── probability ──────────────────────────────│
  │                      │─── INSERT Prediction ─►│                     │
  │                      │◄── pred_id ───────────│                     │
  │◄── redirect /result  │                       │                     │
  │─── GET /result/{id} ─►│                      │                     │
  │                      │─── SELECT * JOIN ────►│                     │
  │                      │◄── full result row ───│                     │
  │◄── Result HTML Page  │                       │                     │
```

---

## Security Architecture

| Threat | Mitigation |
|---|---|
| SQL Injection | Parameterised queries with `%s` placeholders |
| XSS | Jinja2 auto-escaping on all template variables |
| CSRF | POST-only state changes; session validation |
| Brute Force | Login attempt error messages are generic |
| Privilege Escalation | Role checked on every admin route via decorator |
| Password Exposure | bcrypt (PBKDF2-SHA256) via werkzeug |
| Session Hijacking | `SECRET_KEY` required; sessions expire on close |
