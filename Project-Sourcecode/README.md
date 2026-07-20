# Credit Card Approval Prediction System Using Machine Learning

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0-green.svg)](https://flask.palletsprojects.com)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://mysql.com)
[![XGBoost](https://img.shields.io/badge/XGBoost-2.0-red.svg)](https://xgboost.readthedocs.io)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com)

---

## 📌 Overview

A **production-ready, end-to-end web application** that predicts whether a credit card application should be **Approved** or **Rejected** using machine learning. Built with a modern glassmorphism banking UI, secure Flask backend, MySQL database, and four ML models evaluated on multiple metrics.

---

## 🎯 Features

| Feature | Description |
|---|---|
| 🔐 Authentication | Secure login/register with bcrypt password hashing |
| 📋 Application Form | Multi-step validated applicant form |
| 🤖 ML Prediction | Real-time prediction with 4 ML models |
| 📊 Dashboard | Statistics, trend charts, recent predictions |
| 🛡️ Admin Panel | Full CRUD on users, applicants, predictions |
| 📁 CSV Export | Export predictions and users to CSV |
| 📈 Model Comparison | Radar chart + metrics table for all models |
| 🔒 Security | SQL injection prevention, XSS protection, CSRF-safe sessions |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | HTML5, CSS3 (Glassmorphism), Bootstrap 5.3, Chart.js |
| **Backend** | Python 3.10+, Flask 3.0 |
| **Database** | MySQL 8.0 |
| **ML Models** | Logistic Regression, Decision Tree, Random Forest, XGBoost |
| **ML Libraries** | Scikit-learn, XGBoost, Pandas, NumPy, Joblib |
| **Auth** | Werkzeug (bcrypt), Flask Sessions |

---

## 📁 Project Structure

```
Smart Bridge/
│
├── app.py                    # Flask application (all routes)
├── config.py                 # Configuration (env-based)
├── train_model.py            # ML training pipeline
├── schema.sql                # MySQL database schema
├── requirements.txt          # Python dependencies
├── README.md                 # This file
│
├── models/                   # Saved ML model artefacts
│   ├── model.pkl             # Best model pipeline (auto-generated)
│   ├── logistic_regression.pkl
│   ├── decision_tree.pkl
│   ├── random_forest.pkl
│   ├── xgboost.pkl
│   └── metrics.json          # Evaluation metrics (auto-generated)
│
├── static/
│   ├── css/
│   │   └── style.css         # Complete glassmorphism theme
│   └── js/
│       └── main.js           # Charts, animations, UI logic
│
├── templates/
│   ├── base.html             # Base layout (sidebar, topbar)
│   ├── login.html            # Login page
│   ├── register.html         # Registration page
│   ├── dashboard.html        # User dashboard
│   ├── applicant_form.html   # Multi-step application form
│   ├── predict.html          # AI prediction animation page
│   ├── result.html           # Prediction result + gauge
│   ├── history.html          # Prediction history
│   ├── model_info.html       # ML model comparison
│   ├── admin/
│   │   ├── dashboard.html    # Admin overview
│   │   ├── users.html        # User management
│   │   ├── applicants.html   # Applicant management
│   │   └── predictions.html  # Prediction management
│   └── errors/
│       ├── 403.html
│       ├── 404.html
│       └── 500.html
│
├── exports/                  # CSV export directory (auto-created)
└── docs/
    ├── ER_Diagram.md
    ├── Technical_Architecture.md
    ├── Project_Flow.md
    ├── Database_Description.md
    ├── Installation_Guide.md
    └── Future_Scope.md
```

---

## ⚡ Quick Start

### Prerequisites
- Python 3.10+
- MySQL 8.0+
- pip

### Step 1 — Clone / Download the Project
```bash
cd "Smart Bridge"
```

### Step 2 — Create Virtual Environment
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### Step 3 — Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4 — Create MySQL Database
```bash
mysql -u root -p < schema.sql
```

### Step 5 — Configure Environment (optional)
Create a `.env` file or set environment variables:
```env
SECRET_KEY=your_secret_key_here
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=credit_card_db
ADMIN_EMAIL=admin@creditcard.com
ADMIN_PASSWORD=Admin@1234
```

### Step 6 — Train the ML Models
```bash
python train_model.py
```
This will:
- Generate a synthetic credit dataset (5,000 samples)
- Train 4 ML models
- Save the best model as `models/model.pkl`
- Save metrics to `models/metrics.json`

### Step 7 — Run the Application
```bash
python app.py
```

### Step 8 — Access the Application
Open your browser: **http://localhost:5000**

**Default Admin Credentials:**
- Email: `admin@creditcard.com`
- Password: `Admin@1234`

---

## 🤖 Machine Learning Models

| Model | Description |
|---|---|
| Logistic Regression | Linear baseline model with class balancing |
| Decision Tree | Non-linear tree with depth=8, min_samples_split=20 |
| Random Forest | 200-estimator ensemble, depth=10 |
| XGBoost | Gradient boosted trees, lr=0.05, subsample=0.8 |

**Selection Criterion:** Best ROC AUC score on the held-out 20% test set.

**Evaluation Metrics:** Accuracy · Precision · Recall · F1 Score · ROC AUC

---

## 🔒 Security Features

- **Password Hashing** — `werkzeug.security.generate_password_hash` (PBKDF2-SHA256)
- **SQL Injection Prevention** — All queries use parameterised MySQL placeholders (`%s`)
- **XSS Prevention** — Jinja2 auto-escaping enabled for all templates
- **Session Security** — Server-side sessions with `SECRET_KEY`
- **Role-Based Access** — `@login_required` and `@admin_required` decorators
- **Input Validation** — Both client-side (JS) and server-side (Flask) validation

---

## 🗄️ Database Tables

| Table | Description |
|---|---|
| `Users` | Registered users (admin/user roles) |
| `Applicant_Details` | Full applicant profile (income, education, etc.) |
| `Credit_History` | Monthly payment and overdue records |
| `ML_Model` | Trained model metadata and metrics |
| `Approval_Prediction` | Prediction results linked to applicants and models |

---

## 📜 License

This project is developed for academic submission purposes.

---

*Credit Card Approval Prediction System Using Machine Learning — Academic Project 2024*
