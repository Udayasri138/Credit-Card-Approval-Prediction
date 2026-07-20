# Database Description
## Credit Card Approval Prediction System

---

## Database Overview

- **DBMS:** MySQL 8.0
- **Database Name:** `credit_card_db`
- **Character Set:** utf8mb4 (full Unicode, supports emoji)
- **Collation:** utf8mb4_unicode_ci
- **Storage Engine:** InnoDB (ACID-compliant, FK support)
- **Tables:** 5 normalised tables (3NF)
- **Relationships:** 4 foreign key constraints
- **Indexes:** 5 performance indexes

---

## Table 1: Users

**Purpose:** Stores all registered users (admins and regular users).

```sql
CREATE TABLE Users (
    UserID    INT AUTO_INCREMENT PRIMARY KEY,
    Name      VARCHAR(100)  NOT NULL,
    Email     VARCHAR(150)  NOT NULL UNIQUE,
    Password  VARCHAR(255)  NOT NULL,       -- bcrypt hash
    Role      ENUM('admin','user') NOT NULL DEFAULT 'user',
    CreatedAt DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

| Column | Type | Description |
|---|---|---|
| UserID | INT PK | Auto-incrementing primary key |
| Name | VARCHAR(100) | Full name of the user |
| Email | VARCHAR(150) UNIQUE | Login identifier |
| Password | VARCHAR(255) | PBKDF2-SHA256 hash (bcrypt via werkzeug) |
| Role | ENUM | 'admin' has full access; 'user' has restricted access |
| CreatedAt | DATETIME | Account registration timestamp |

---

## Table 2: Applicant_Details

**Purpose:** Stores the complete profile of each credit card applicant.

```sql
CREATE TABLE Applicant_Details (
    ApplicantID       INT AUTO_INCREMENT PRIMARY KEY,
    UserID            INT NOT NULL,       -- FK → Users
    FullName          VARCHAR(100) NOT NULL,
    Age               INT NOT NULL,
    Gender            ENUM('Male','Female','Other') NOT NULL,
    AnnualIncome      DECIMAL(15,2) NOT NULL,
    IncomeType        ENUM(...) NOT NULL,
    EducationType     ENUM(...) NOT NULL,
    FamilyStatus      ENUM(...) NOT NULL,
    HousingType       ENUM(...) NOT NULL,
    EmploymentDays    INT NOT NULL,       -- +ve = employed, -ve = unemployed
    OwnsCar           TINYINT(1) NOT NULL DEFAULT 0,
    OwnsProperty      TINYINT(1) NOT NULL DEFAULT 0,
    NumChildren       INT NOT NULL DEFAULT 0,
    FamilyMemberCount INT NOT NULL DEFAULT 1,
    WorkPhoneProvided TINYINT(1) NOT NULL DEFAULT 0,
    PhoneProvided     TINYINT(1) NOT NULL DEFAULT 0,
    EmailProvided     TINYINT(1) NOT NULL DEFAULT 1,
    SubmittedAt       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
);
```

**Key Design Decisions:**
- `EmploymentDays`: Positive values indicate active employment duration; negative values indicate days elapsed since job ended
- `TINYINT(1)` used for boolean fields to minimise storage
- `DECIMAL(15,2)` for income to handle large values precisely
- `ON DELETE CASCADE` ensures that deleting a user removes all their applications

---

## Table 3: Credit_History

**Purpose:** Records past credit payment behaviour for each applicant.

```sql
CREATE TABLE Credit_History (
    HistoryID     INT AUTO_INCREMENT PRIMARY KEY,
    ApplicantID   INT NOT NULL,           -- FK → Applicant_Details
    MonthsBalance INT NOT NULL,           -- 0=current, -1=last month, etc.
    PaymentStatus ENUM('0','1','2','3','4','5','C','X') NOT NULL,
    OverdueStatus ENUM(...) NOT NULL DEFAULT 'No overdue',
    RecordedAt    DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ApplicantID) REFERENCES Applicant_Details(ApplicantID) ON DELETE CASCADE
);
```

**PaymentStatus Values:**
| Value | Meaning |
|---|---|
| C | Paid off that month |
| X | No loan that month |
| 0 | Current (no overdue) |
| 1–5 | 1–5 months overdue |

---

## Table 4: ML_Model

**Purpose:** Stores metadata and performance metrics for all trained ML models.

```sql
CREATE TABLE ML_Model (
    ModelID         INT AUTO_INCREMENT PRIMARY KEY,
    ModelName       VARCHAR(100) NOT NULL,
    AlgorithmType   VARCHAR(100) NOT NULL,
    Accuracy        DECIMAL(6,4) NOT NULL,
    Precision_Score DECIMAL(6,4) NOT NULL DEFAULT 0.0,
    Recall_Score    DECIMAL(6,4) NOT NULL DEFAULT 0.0,
    F1_Score        DECIMAL(6,4) NOT NULL DEFAULT 0.0,
    ROC_AUC         DECIMAL(6,4) NOT NULL DEFAULT 0.0,
    ModelFile       VARCHAR(255) NOT NULL,
    IsBestModel     TINYINT(1)   NOT NULL DEFAULT 0,
    TrainedAt       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

**Populated by:** `train_model.py` via `models/metrics.json` seed on app startup.
**IsBestModel:** Only one record has `IsBestModel=1` — the model with the highest ROC AUC.

---

## Table 5: Approval_Prediction

**Purpose:** Stores the ML prediction result for each credit card application.

```sql
CREATE TABLE Approval_Prediction (
    PredictionID    INT AUTO_INCREMENT PRIMARY KEY,
    ApplicantID     INT NOT NULL,           -- FK → Applicant_Details
    ModelID         INT NOT NULL,           -- FK → ML_Model
    ApprovalResult  ENUM('Approved','Rejected') NOT NULL,
    RiskCategory    ENUM('Low Risk','Medium Risk','High Risk') NOT NULL,
    ConfidenceScore DECIMAL(5,2) NOT NULL DEFAULT 0.00,   -- 0.00–100.00
    PredictionDate  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ApplicantID) REFERENCES Applicant_Details(ApplicantID) ON DELETE CASCADE,
    FOREIGN KEY (ModelID)     REFERENCES ML_Model(ModelID) ON DELETE RESTRICT
);
```

**Risk Category Logic:**
| Confidence Score | Risk Category |
|---|---|
| ≥ 75% | Low Risk |
| 45% – 74% | Medium Risk |
| < 45% | High Risk |

---

## Indexes

| Index Name | Table | Column(s) | Purpose |
|---|---|---|---|
| idx_applicant_user | Applicant_Details | UserID | Fast user-specific queries |
| idx_history_app | Credit_History | ApplicantID | Fast history lookup |
| idx_prediction_app | Approval_Prediction | ApplicantID | Fast prediction lookup |
| idx_prediction_model | Approval_Prediction | ModelID | Join performance |
| idx_prediction_date | Approval_Prediction | PredictionDate | Date-range queries |
