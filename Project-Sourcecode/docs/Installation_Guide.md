# Installation Guide
## Credit Card Approval Prediction System

---

## System Requirements

| Component | Minimum | Recommended |
|---|---|---|
| Python | 3.10 | 3.11+ |
| MySQL | 8.0 | 8.0.33+ |
| RAM | 4 GB | 8 GB |
| Disk | 500 MB | 1 GB |
| OS | Windows 10 / Ubuntu 20.04 | Windows 11 / Ubuntu 22.04 |

---

## Step-by-Step Installation

### Step 1: Verify Python Installation
```bash
python --version
# Should output: Python 3.10.x or higher

pip --version
# Should output: pip 23.x or higher
```

If Python is not installed, download from: https://python.org/downloads/

---

### Step 2: Verify MySQL Installation
```bash
mysql --version
# Should output: mysql  Ver 8.0.x
```

If MySQL is not installed:
- **Windows:** Download MySQL Installer from https://dev.mysql.com/downloads/installer/
- **Ubuntu:** `sudo apt install mysql-server`

Start MySQL service:
- **Windows:** `net start MySQL80` (or use MySQL Workbench / XAMPP)
- **Ubuntu:** `sudo systemctl start mysql`

---

### Step 3: Set Up the Project

```bash
# Navigate to project directory
cd "Smart Bridge"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows PowerShell:
venv\Scripts\Activate.ps1
# Windows CMD:
venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate

# You should see (venv) in your terminal prompt
```

---

### Step 4: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs: Flask, MySQL Connector, Pandas, NumPy, Scikit-learn, XGBoost, Joblib, Werkzeug, etc.

Verify key packages:
```bash
python -c "import flask, sklearn, xgboost, pandas; print('All OK')"
```

---

### Step 5: Create MySQL Database

Option A — Using command line:
```bash
mysql -u root -p < schema.sql
```

Option B — Using MySQL Workbench:
1. Open MySQL Workbench
2. Connect to your MySQL server
3. File → Open SQL Script → Select `schema.sql`
4. Click the ⚡ (Execute) button

Option C — Manual:
```sql
-- Run these in MySQL shell or Workbench:
CREATE DATABASE credit_card_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE credit_card_db;
SOURCE schema.sql;
```

Verify tables were created:
```sql
USE credit_card_db;
SHOW TABLES;
-- Should show: Users, Applicant_Details, Credit_History, ML_Model, Approval_Prediction
```

---

### Step 6: Configure Environment Variables

Create a `.env` file in the project root:
```bash
# .env
SECRET_KEY=change_this_to_a_random_64_char_string
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_root_password
DB_NAME=credit_card_db
DB_PORT=3306
ADMIN_EMAIL=admin@creditcard.com
ADMIN_PASSWORD=Admin@1234
ADMIN_NAME=System Administrator
DEBUG=True
```

> **Note:** If you don't create `.env`, the app will use defaults from `config.py`.
> You MUST set `DB_PASSWORD` to match your MySQL root password.

---

### Step 7: Train the ML Models

```bash
python train_model.py
```

Expected output:
```
=================================================================
  Credit Card Approval Prediction — ML Training Pipeline
=================================================================

[1/6] Generating synthetic dataset (5,000 samples)…
[2/6] Preprocessing (clean, encode, engineer features)…
[3/6] Splitting: 80% train / 20% test (stratified)…
[4/6] Training and evaluating 4 models…

  Model                     Acc    Prec  Recall      F1     AUC
-----------------------------------------------------------------
  Logistic Regression    0.8xxx  0.8xxx  0.8xxx  0.8xxx  0.8xxx
  Decision Tree          0.8xxx  0.8xxx  0.8xxx  0.8xxx  0.8xxx
  Random Forest          0.8xxx  0.8xxx  0.8xxx  0.8xxx  0.9xxx
  XGBoost                0.8xxx  0.8xxx  0.8xxx  0.8xxx  0.9xxx

[5/6] Best model: Random Forest / XGBoost
[6/6] Saving model artefacts…
      Saved: models/logistic_regression.pkl
      Saved: models/decision_tree.pkl
      Saved: models/random_forest.pkl
      Saved: models/xgboost.pkl
      Saved: models/model.pkl  ← BEST MODEL PIPELINE
      Saved: models/metrics.json
```

---

### Step 8: Run the Application

```bash
python app.py
```

Expected output:
```
[SEED] Admin created: admin@creditcard.com
[SEED] ML model records inserted.
 * Running on http://0.0.0.0:5000
 * Debug mode: on
```

---

### Step 9: Access the Application

Open your browser and navigate to:
**http://localhost:5000**

You will be redirected to the login page.

**Admin Login:**
- Email: `admin@creditcard.com`
- Password: `Admin@1234`

**To create a regular user account:**
Click "Create Account" on the login page and register.

---

## Troubleshooting

### MySQL Connection Error
```
mysql.connector.errors.DatabaseError: 2003 (HY000): Can't connect to MySQL server
```
**Fix:** Ensure MySQL service is running.
```bash
# Windows
net start MySQL80
# Ubuntu
sudo systemctl start mysql
```

### Module Not Found Error
```
ModuleNotFoundError: No module named 'xgboost'
```
**Fix:** Activate the virtual environment first, then install:
```bash
venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

### model.pkl Not Found
```
ML model not found. Please run train_model.py first.
```
**Fix:** Run the training script:
```bash
python train_model.py
```

### Port Already in Use
```
OSError: [Errno 98] Address already in use: port 5000
```
**Fix:** Change the port or kill the process using port 5000:
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux
lsof -i :5000
kill -9 <PID>
```
Or change port in `app.py`:
```python
app.run(debug=True, port=5001)
```

### Access Denied (MySQL)
**Fix:** Use the correct MySQL user and password in `.env`.
```bash
mysql -u root -p
# Enter your MySQL root password when prompted
```

---

## Production Deployment Notes

For production deployment (not required for academic submission):

1. Set `DEBUG=False` in `.env`
2. Use Gunicorn: `gunicorn -w 4 -b 0.0.0.0:5000 app:app`
3. Use Nginx as reverse proxy
4. Use a connection pool (e.g., `mysql.connector.pooling`)
5. Store `SECRET_KEY` in a secure secrets manager
6. Enable HTTPS with Let's Encrypt
