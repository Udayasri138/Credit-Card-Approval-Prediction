# ER Diagram Description
## Credit Card Approval Prediction System

---

## Entities and Attributes

### 1. Users
| Attribute | Type | Key | Notes |
|---|---|---|---|
| UserID | INT | PK, AUTO_INCREMENT | Unique user identifier |
| Name | VARCHAR(100) | — | Full name |
| Email | VARCHAR(150) | UNIQUE | Login credential |
| Password | VARCHAR(255) | — | bcrypt hash |
| Role | ENUM | — | 'admin' or 'user' |
| CreatedAt | DATETIME | — | Account creation timestamp |

### 2. Applicant_Details
| Attribute | Type | Key | Notes |
|---|---|---|---|
| ApplicantID | INT | PK, AUTO_INCREMENT | Unique applicant ID |
| UserID | INT | FK → Users.UserID | Submitting user |
| FullName | VARCHAR(100) | — | Applicant legal name |
| Age | INT | — | 18–80 years |
| Gender | ENUM | — | Male/Female/Other |
| AnnualIncome | DECIMAL(15,2) | — | In INR |
| IncomeType | ENUM | — | Working/Pensioner/etc. |
| EducationType | ENUM | — | Highest qualification |
| FamilyStatus | ENUM | — | Married/Single/etc. |
| HousingType | ENUM | — | Accommodation type |
| EmploymentDays | INT | — | +ve=employed, -ve=unemployed |
| OwnsCar | TINYINT(1) | — | Boolean |
| OwnsProperty | TINYINT(1) | — | Boolean |
| NumChildren | INT | — | Number of dependants |
| FamilyMemberCount | INT | — | Total household |
| WorkPhoneProvided | TINYINT(1) | — | Boolean |
| PhoneProvided | TINYINT(1) | — | Boolean |
| EmailProvided | TINYINT(1) | — | Boolean |
| SubmittedAt | DATETIME | — | Submission timestamp |

### 3. Credit_History
| Attribute | Type | Key | Notes |
|---|---|---|---|
| HistoryID | INT | PK, AUTO_INCREMENT | Unique history record |
| ApplicantID | INT | FK → Applicant_Details.ApplicantID | |
| MonthsBalance | INT | — | 0=current, -1=one month ago |
| PaymentStatus | ENUM | — | 0–5=overdue, C=paid, X=no loan |
| OverdueStatus | ENUM | — | Categorised overdue level |
| RecordedAt | DATETIME | — | Record timestamp |

### 4. ML_Model
| Attribute | Type | Key | Notes |
|---|---|---|---|
| ModelID | INT | PK, AUTO_INCREMENT | Unique model ID |
| ModelName | VARCHAR(100) | — | Human-readable name |
| AlgorithmType | VARCHAR(100) | — | e.g. 'xgboost' |
| Accuracy | DECIMAL(6,4) | — | Test set accuracy (0–1) |
| Precision_Score | DECIMAL(6,4) | — | Precision metric |
| Recall_Score | DECIMAL(6,4) | — | Recall metric |
| F1_Score | DECIMAL(6,4) | — | F1 harmonic mean |
| ROC_AUC | DECIMAL(6,4) | — | Area under ROC curve |
| ModelFile | VARCHAR(255) | — | Relative path to .pkl |
| IsBestModel | TINYINT(1) | — | 1 = currently deployed |
| TrainedAt | DATETIME | — | Training timestamp |

### 5. Approval_Prediction
| Attribute | Type | Key | Notes |
|---|---|---|---|
| PredictionID | INT | PK, AUTO_INCREMENT | Unique prediction ID |
| ApplicantID | INT | FK → Applicant_Details.ApplicantID | |
| ModelID | INT | FK → ML_Model.ModelID | |
| ApprovalResult | ENUM | — | 'Approved' or 'Rejected' |
| RiskCategory | ENUM | — | Low/Medium/High Risk |
| ConfidenceScore | DECIMAL(5,2) | — | 0.00–100.00 % |
| PredictionDate | DATETIME | — | Prediction timestamp |

---

## Relationships

```
Users ─────────────────────────── Applicant_Details
  1                                        N
  (One user can submit many applications)

Applicant_Details ─────────────── Credit_History
       1                               N
  (One applicant has many credit history records)

Applicant_Details ─────────────── Approval_Prediction
       1                               1
  (One applicant has one prediction result)

ML_Model ──────────────────────── Approval_Prediction
   1                                      N
  (One model is used for many predictions)
```

---

## ER Diagram (Text Notation)

```
┌──────────────────────┐         ┌──────────────────────────────────┐
│        Users         │         │        Applicant_Details          │
├──────────────────────┤         ├──────────────────────────────────┤
│ PK  UserID           │◄────1──N│ PK  ApplicantID                  │
│     Name             │         │ FK  UserID                       │
│     Email            │         │     FullName                     │
│     Password         │         │     Age / Gender                 │
│     Role             │         │     AnnualIncome / IncomeType    │
│     CreatedAt        │         │     EducationType / FamilyStatus │
└──────────────────────┘         │     HousingType / EmploymentDays │
                                  │     OwnsCar / OwnsProperty       │
                                  │     NumChildren / FamilyCount    │
                                  │     SubmittedAt                  │
                                  └─────────────┬──────────────┬────┘
                                                │1             │1
                                               N│             │1
                                  ┌─────────────▼──────┐ ┌────▼──────────────────────┐
                                  │   Credit_History    │ │    Approval_Prediction     │
                                  ├────────────────────┤ ├────────────────────────────┤
                                  │ PK HistoryID       │ │ PK PredictionID            │
                                  │ FK ApplicantID     │ │ FK ApplicantID             │
                                  │    MonthsBalance   │ │ FK ModelID ◄──────────────┐│
                                  │    PaymentStatus   │ │    ApprovalResult          ││
                                  │    OverdueStatus   │ │    RiskCategory            ││
                                  │    RecordedAt      │ │    ConfidenceScore         ││
                                  └────────────────────┘ │    PredictionDate          ││
                                                          └────────────────────────────┘│
                                                          ┌─────────────────────────────┘
                                                          │          ML_Model
                                                          │  ┌──────────────────────────┐
                                                          └─N│ PK  ModelID              │
                                                             │     ModelName            │
                                                             │     AlgorithmType        │
                                                             │     Accuracy             │
                                                             │     Precision_Score      │
                                                             │     Recall_Score         │
                                                             │     F1_Score / ROC_AUC   │
                                                             │     ModelFile            │
                                                             │     IsBestModel          │
                                                             │     TrainedAt            │
                                                             └──────────────────────────┘
```

---

## Cardinality Summary

| Relationship | Type | Enforced By |
|---|---|---|
| Users → Applicant_Details | 1:N | FK with ON DELETE CASCADE |
| Applicant_Details → Credit_History | 1:N | FK with ON DELETE CASCADE |
| Applicant_Details → Approval_Prediction | 1:1 (application level) | FK with ON DELETE CASCADE |
| ML_Model → Approval_Prediction | 1:N | FK with ON DELETE RESTRICT |
