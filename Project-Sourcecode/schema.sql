-- ============================================================
-- Credit Card Approval Prediction System
-- Database Schema
-- ============================================================

CREATE DATABASE IF NOT EXISTS credit_card_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE credit_card_db;

-- ============================================================
-- Table 1: Users
-- ============================================================
CREATE TABLE IF NOT EXISTS Users (
    UserID      INT AUTO_INCREMENT PRIMARY KEY,
    Name        VARCHAR(100)  NOT NULL,
    Email       VARCHAR(150)  NOT NULL UNIQUE,
    Password    VARCHAR(255)  NOT NULL,
    Role        ENUM('admin','user') NOT NULL DEFAULT 'user',
    CreatedAt   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Table 2: Applicant_Details
-- ============================================================
CREATE TABLE IF NOT EXISTS Applicant_Details (
    ApplicantID         INT AUTO_INCREMENT PRIMARY KEY,
    UserID              INT          NOT NULL,
    FullName            VARCHAR(100) NOT NULL,
    Age                 INT          NOT NULL,
    Gender              ENUM('Male','Female','Other') NOT NULL,
    AnnualIncome        DECIMAL(15,2) NOT NULL,
    IncomeType          ENUM('Working','Commercial associate','Pensioner','State servant','Student') NOT NULL,
    EducationType       ENUM('Higher education','Secondary / secondary special','Incomplete higher','Lower secondary','Academic degree') NOT NULL,
    FamilyStatus        ENUM('Married','Single / not married','Civil marriage','Separated','Widow') NOT NULL,
    HousingType         ENUM('House / apartment','With parents','Municipal apartment','Rented apartment','Office apartment','Co-op apartment') NOT NULL,
    EmploymentDays      INT          NOT NULL COMMENT 'Positive = employed days, Negative = unemployed (days since last job)',
    OwnsCar             TINYINT(1)   NOT NULL DEFAULT 0,
    OwnsProperty        TINYINT(1)   NOT NULL DEFAULT 0,
    NumChildren         INT          NOT NULL DEFAULT 0,
    FamilyMemberCount   INT          NOT NULL DEFAULT 1,
    WorkPhoneProvided   TINYINT(1)   NOT NULL DEFAULT 0,
    PhoneProvided       TINYINT(1)   NOT NULL DEFAULT 0,
    EmailProvided       TINYINT(1)   NOT NULL DEFAULT 1,
    SubmittedAt         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_applicant_user FOREIGN KEY (UserID) REFERENCES Users(UserID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Table 3: Credit_History
-- ============================================================
CREATE TABLE IF NOT EXISTS Credit_History (
    HistoryID       INT AUTO_INCREMENT PRIMARY KEY,
    ApplicantID     INT  NOT NULL,
    MonthsBalance   INT  NOT NULL COMMENT '0 = current month, -1 = one month ago, etc.',
    PaymentStatus   ENUM('0','1','2','3','4','5','C','X') NOT NULL
                    COMMENT '0-5=overdue months, C=paid off that month, X=no loan that month',
    OverdueStatus   ENUM('No overdue','1-29 days overdue','30-59 days overdue','60-89 days overdue','90+ days overdue') NOT NULL DEFAULT 'No overdue',
    RecordedAt      DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_history_applicant FOREIGN KEY (ApplicantID) REFERENCES Applicant_Details(ApplicantID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Table 4: ML_Model
-- ============================================================
CREATE TABLE IF NOT EXISTS ML_Model (
    ModelID         INT AUTO_INCREMENT PRIMARY KEY,
    ModelName       VARCHAR(100)   NOT NULL,
    AlgorithmType   VARCHAR(100)   NOT NULL,
    Accuracy        DECIMAL(6,4)   NOT NULL,
    Precision_Score DECIMAL(6,4)   NOT NULL DEFAULT 0.0,
    Recall_Score    DECIMAL(6,4)   NOT NULL DEFAULT 0.0,
    F1_Score        DECIMAL(6,4)   NOT NULL DEFAULT 0.0,
    ROC_AUC         DECIMAL(6,4)   NOT NULL DEFAULT 0.0,
    ModelFile       VARCHAR(255)   NOT NULL,
    IsBestModel     TINYINT(1)     NOT NULL DEFAULT 0,
    TrainedAt       DATETIME       NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Table 5: Approval_Prediction
-- ============================================================
CREATE TABLE IF NOT EXISTS Approval_Prediction (
    PredictionID    INT AUTO_INCREMENT PRIMARY KEY,
    ApplicantID     INT                         NOT NULL,
    ModelID         INT                         NOT NULL,
    ApprovalResult  ENUM('Approved','Rejected') NOT NULL,
    RiskCategory    ENUM('Low Risk','Medium Risk','High Risk') NOT NULL,
    ConfidenceScore DECIMAL(5,2)                NOT NULL DEFAULT 0.00 COMMENT 'Probability 0-100',
    PredictionDate  DATETIME                    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_prediction_applicant FOREIGN KEY (ApplicantID) REFERENCES Applicant_Details(ApplicantID) ON DELETE CASCADE,
    CONSTRAINT fk_prediction_model     FOREIGN KEY (ModelID)      REFERENCES ML_Model(ModelID) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================================
-- Indexes for performance
-- ============================================================
CREATE INDEX idx_applicant_user   ON Applicant_Details(UserID);
CREATE INDEX idx_history_app      ON Credit_History(ApplicantID);
CREATE INDEX idx_prediction_app   ON Approval_Prediction(ApplicantID);
CREATE INDEX idx_prediction_model ON Approval_Prediction(ModelID);
CREATE INDEX idx_prediction_date  ON Approval_Prediction(PredictionDate);
