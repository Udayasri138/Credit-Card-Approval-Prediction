-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Jul 19, 2026 at 09:46 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `credit_card_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `applicant_details`
--

CREATE TABLE `applicant_details` (
  `ApplicantID` int(11) NOT NULL,
  `UserID` int(11) NOT NULL,
  `FullName` varchar(100) NOT NULL,
  `Age` int(11) NOT NULL,
  `Gender` enum('Male','Female','Other') NOT NULL,
  `AnnualIncome` decimal(15,2) NOT NULL,
  `IncomeType` enum('Working','Commercial associate','Pensioner','State servant','Student') NOT NULL,
  `EducationType` enum('Higher education','Secondary / secondary special','Incomplete higher','Lower secondary','Academic degree') NOT NULL,
  `FamilyStatus` enum('Married','Single / not married','Civil marriage','Separated','Widow') NOT NULL,
  `HousingType` enum('House / apartment','With parents','Municipal apartment','Rented apartment','Office apartment','Co-op apartment') NOT NULL,
  `EmploymentDays` int(11) NOT NULL COMMENT 'Positive = employed days, Negative = unemployed (days since last job)',
  `OwnsCar` tinyint(1) NOT NULL DEFAULT 0,
  `OwnsProperty` tinyint(1) NOT NULL DEFAULT 0,
  `NumChildren` int(11) NOT NULL DEFAULT 0,
  `FamilyMemberCount` int(11) NOT NULL DEFAULT 1,
  `WorkPhoneProvided` tinyint(1) NOT NULL DEFAULT 0,
  `PhoneProvided` tinyint(1) NOT NULL DEFAULT 0,
  `EmailProvided` tinyint(1) NOT NULL DEFAULT 1,
  `SubmittedAt` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `applicant_details`
--

INSERT INTO `applicant_details` (`ApplicantID`, `UserID`, `FullName`, `Age`, `Gender`, `AnnualIncome`, `IncomeType`, `EducationType`, `FamilyStatus`, `HousingType`, `EmploymentDays`, `OwnsCar`, `OwnsProperty`, `NumChildren`, `FamilyMemberCount`, `WorkPhoneProvided`, `PhoneProvided`, `EmailProvided`, `SubmittedAt`) VALUES
(1, 1, 'Alice Cooper', 32, 'Female', 540000.00, 'Working', 'Higher education', 'Married', 'House / apartment', 1500, 1, 1, 0, 2, 0, 0, 1, '2026-07-14 20:06:33'),
(2, 1, 'Alice Cooper', 32, 'Female', 540000.00, 'Working', 'Higher education', 'Married', 'House / apartment', 1500, 0, 0, 0, 2, 0, 0, 1, '2026-07-14 20:09:22'),
(3, 1, 'Alice Cooper', 32, 'Female', 540000.00, 'Working', 'Higher education', 'Married', 'House / apartment', 1500, 0, 0, 0, 2, 0, 0, 0, '2026-07-14 20:12:33'),
(4, 1, 'Alice Cooper', 32, 'Female', 540000.00, 'Working', 'Higher education', 'Married', 'House / apartment', 1500, 1, 1, 0, 2, 0, 0, 1, '2026-07-14 20:19:41'),
(5, 1, 'Test Applicant', 25, 'Female', 54000.00, 'Working', 'Higher education', 'Single / not married', 'Rented apartment', 1200, 1, 0, 0, 1, 0, 1, 1, '2026-07-19 12:54:46');

-- --------------------------------------------------------

--
-- Table structure for table `approval_prediction`
--

CREATE TABLE `approval_prediction` (
  `PredictionID` int(11) NOT NULL,
  `ApplicantID` int(11) NOT NULL,
  `ModelID` int(11) NOT NULL,
  `ApprovalResult` enum('Approved','Rejected') NOT NULL,
  `RiskCategory` enum('Low Risk','Medium Risk','High Risk') NOT NULL,
  `ConfidenceScore` decimal(5,2) NOT NULL DEFAULT 0.00 COMMENT 'Probability 0-100',
  `PredictionDate` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `approval_prediction`
--

INSERT INTO `approval_prediction` (`PredictionID`, `ApplicantID`, `ModelID`, `ApprovalResult`, `RiskCategory`, `ConfidenceScore`, `PredictionDate`) VALUES
(1, 3, 1, 'Approved', 'Low Risk', 98.53, '2026-07-14 20:12:37'),
(2, 4, 1, 'Approved', 'Low Risk', 99.80, '2026-07-14 20:19:51');

-- --------------------------------------------------------

--
-- Table structure for table `credit_history`
--

CREATE TABLE `credit_history` (
  `HistoryID` int(11) NOT NULL,
  `ApplicantID` int(11) NOT NULL,
  `MonthsBalance` int(11) NOT NULL COMMENT '0 = current month, -1 = one month ago, etc.',
  `PaymentStatus` enum('0','1','2','3','4','5','C','X') NOT NULL COMMENT '0-5=overdue months, C=paid off that month, X=no loan that month',
  `OverdueStatus` enum('No overdue','1-29 days overdue','30-59 days overdue','60-89 days overdue','90+ days overdue') NOT NULL DEFAULT 'No overdue',
  `RecordedAt` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `credit_history`
--

INSERT INTO `credit_history` (`HistoryID`, `ApplicantID`, `MonthsBalance`, `PaymentStatus`, `OverdueStatus`, `RecordedAt`) VALUES
(1, 1, -12, 'C', 'No overdue', '2026-07-14 20:06:33'),
(2, 2, -12, 'C', 'No overdue', '2026-07-14 20:09:22'),
(3, 3, -12, 'C', 'No overdue', '2026-07-14 20:12:33'),
(4, 4, -12, 'C', 'No overdue', '2026-07-14 20:19:41'),
(5, 5, -12, 'C', 'No overdue', '2026-07-19 12:54:46');

-- --------------------------------------------------------

--
-- Table structure for table `ml_model`
--

CREATE TABLE `ml_model` (
  `ModelID` int(11) NOT NULL,
  `ModelName` varchar(100) NOT NULL,
  `AlgorithmType` varchar(100) NOT NULL,
  `Accuracy` decimal(6,4) NOT NULL,
  `Precision_Score` decimal(6,4) NOT NULL DEFAULT 0.0000,
  `Recall_Score` decimal(6,4) NOT NULL DEFAULT 0.0000,
  `F1_Score` decimal(6,4) NOT NULL DEFAULT 0.0000,
  `ROC_AUC` decimal(6,4) NOT NULL DEFAULT 0.0000,
  `ModelFile` varchar(255) NOT NULL,
  `IsBestModel` tinyint(1) NOT NULL DEFAULT 0,
  `TrainedAt` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `ml_model`
--

INSERT INTO `ml_model` (`ModelID`, `ModelName`, `AlgorithmType`, `Accuracy`, `Precision_Score`, `Recall_Score`, `F1_Score`, `ROC_AUC`, `ModelFile`, `IsBestModel`, `TrainedAt`) VALUES
(1, 'Logistic Regression', 'logistic_regression', 0.8220, 0.6029, 0.8440, 0.7033, 0.9135, 'models/logistic_regression.pkl', 1, '2026-07-14 19:57:17'),
(2, 'Decision Tree', 'decision_tree', 0.8120, 0.5876, 0.8320, 0.6887, 0.8678, 'models/decision_tree.pkl', 0, '2026-07-14 19:57:17'),
(3, 'Random Forest', 'random_forest', 0.8450, 0.6498, 0.8240, 0.7266, 0.9107, 'models/random_forest.pkl', 0, '2026-07-14 19:57:17'),
(4, 'XGBoost', 'xgboost', 0.8640, 0.7568, 0.6720, 0.7119, 0.9134, 'models/xgboost.pkl', 0, '2026-07-14 19:57:17');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `UserID` int(11) NOT NULL,
  `Name` varchar(100) NOT NULL,
  `Email` varchar(150) NOT NULL,
  `Password` varchar(255) NOT NULL,
  `Role` enum('admin','user') NOT NULL DEFAULT 'user',
  `CreatedAt` datetime NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`UserID`, `Name`, `Email`, `Password`, `Role`, `CreatedAt`) VALUES
(1, 'System Administrator', 'admin@creditcard.com', 'scrypt:32768:8:1$HkvlpQpjzcr5iDQL$f7dce295a4a4377a213caa315f889fabfc648f4b28529c44cad1e097e5e953e63399a922dc060f01770040bad7ef773e82eadd7af73076b648e852e6b1b808f8', 'admin', '2026-07-14 19:57:17'),
(2, 'Mahesh D', 'maheshd3846@gmail.com', 'scrypt:32768:8:1$S3L3L1Y3Xua2vWsc$fd7e3be51d36a0e588307cec1490e7445ddd99969c38e5b3d73bc6f7e605aa28a60e3e667bf5df19400c85cb4bf2614929ed3597e2e6e9bfba72774a4111c51c', 'user', '2026-07-14 20:23:59');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `applicant_details`
--
ALTER TABLE `applicant_details`
  ADD PRIMARY KEY (`ApplicantID`),
  ADD KEY `idx_applicant_user` (`UserID`);

--
-- Indexes for table `approval_prediction`
--
ALTER TABLE `approval_prediction`
  ADD PRIMARY KEY (`PredictionID`),
  ADD KEY `idx_prediction_app` (`ApplicantID`),
  ADD KEY `idx_prediction_model` (`ModelID`),
  ADD KEY `idx_prediction_date` (`PredictionDate`);

--
-- Indexes for table `credit_history`
--
ALTER TABLE `credit_history`
  ADD PRIMARY KEY (`HistoryID`),
  ADD KEY `idx_history_app` (`ApplicantID`);

--
-- Indexes for table `ml_model`
--
ALTER TABLE `ml_model`
  ADD PRIMARY KEY (`ModelID`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`UserID`),
  ADD UNIQUE KEY `Email` (`Email`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `applicant_details`
--
ALTER TABLE `applicant_details`
  MODIFY `ApplicantID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `approval_prediction`
--
ALTER TABLE `approval_prediction`
  MODIFY `PredictionID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `credit_history`
--
ALTER TABLE `credit_history`
  MODIFY `HistoryID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `ml_model`
--
ALTER TABLE `ml_model`
  MODIFY `ModelID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `UserID` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=23;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `applicant_details`
--
ALTER TABLE `applicant_details`
  ADD CONSTRAINT `fk_applicant_user` FOREIGN KEY (`UserID`) REFERENCES `users` (`UserID`) ON DELETE CASCADE;

--
-- Constraints for table `approval_prediction`
--
ALTER TABLE `approval_prediction`
  ADD CONSTRAINT `fk_prediction_applicant` FOREIGN KEY (`ApplicantID`) REFERENCES `applicant_details` (`ApplicantID`) ON DELETE CASCADE,
  ADD CONSTRAINT `fk_prediction_model` FOREIGN KEY (`ModelID`) REFERENCES `ml_model` (`ModelID`);

--
-- Constraints for table `credit_history`
--
ALTER TABLE `credit_history`
  ADD CONSTRAINT `fk_history_applicant` FOREIGN KEY (`ApplicantID`) REFERENCES `applicant_details` (`ApplicantID`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
