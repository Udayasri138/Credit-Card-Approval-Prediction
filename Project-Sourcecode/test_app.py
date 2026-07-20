import unittest
import os
import re
from flask import session
from app import app, get_db, query_db

class CreditAITestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set testing configuration
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False
        cls.db = get_db()
        cls.cleanup_test_data()

    @classmethod
    def tearDownClass(cls):
        cls.cleanup_test_data()
        cls.db.close()

    @classmethod
    def cleanup_test_data(cls):
        """Clean up any database records created by the tests."""
        try:
            # Cascading deletes will remove applicants, predictions, and credit histories automatically
            cursor = cls.db.cursor()
            cursor.execute("DELETE FROM Users WHERE Email LIKE 'test_%@test.com'")
            cls.db.commit()
            cursor.close()
        except Exception as e:
            cls.db.rollback()
            print(f"Cleanup error: {e}")

    def setUp(self):
        self.client = app.test_client()
        # Clean up database records before each test for fresh execution context
        self.cleanup_test_data()

    def tearDown(self):
        self.cleanup_test_data()

    def test_landing_page_redirects(self):
        """Anonymous user should be redirected to login page."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login", response.location)

    def test_custom_404(self):
        """Accessing a non-existent URL should render a 404 page."""
        response = self.client.get("/non_existent_page_12345")
        self.assertEqual(response.status_code, 404)
        self.assertIn(b"Page Not Found", response.data)

    def test_registration_validation(self):
        """Test registration error handling for invalid user inputs."""
        # Short password
        res = self.client.post("/register", data={
            "name": "Test User",
            "email": "test_register@test.com",
            "password": "short",
            "confirm_password": "short"
        }, follow_redirects=True)
        self.assertIn(b"Password must be at least 8 characters", res.data)

        # Mismatched password
        res = self.client.post("/register", data={
            "name": "Test User",
            "email": "test_register@test.com",
            "password": "valid_password",
            "confirm_password": "mismatched_password"
        }, follow_redirects=True)
        self.assertIn(b"Passwords do not match", res.data)

    def test_registration_success_and_duplicate(self):
        """Test successful registration and duplicate email check."""
        res = self.client.post("/register", data={
            "name": "Test User",
            "email": "test_new_user@test.com",
            "password": "secure_password",
            "confirm_password": "secure_password"
        }, follow_redirects=True)
        self.assertIn(b"Registration successful", res.data)

        # Register again with duplicate email
        res = self.client.post("/register", data={
            "name": "Another Name",
            "email": "test_new_user@test.com",
            "password": "secure_password",
            "confirm_password": "secure_password"
        }, follow_redirects=True)
        self.assertIn(b"An account with that email already exists", res.data)

    def test_login_validation_and_success(self):
        """Test user login validation and success flow."""
        # Register a test user first
        self.client.post("/register", data={
            "name": "Login Tester",
            "email": "test_login@test.com",
            "password": "test_password",
            "confirm_password": "test_password"
        })

        # Login failure
        res = self.client.post("/login", data={
            "email": "test_login@test.com",
            "password": "wrong_password"
        }, follow_redirects=True)
        self.assertIn(b"Invalid email or password", res.data)

        # Login success
        res = self.client.post("/login", data={
            "email": "test_login@test.com",
            "password": "test_password"
        }, follow_redirects=True)
        self.assertIn(b"Welcome back", res.data)

    def test_unauthenticated_restrictions(self):
        """Unauthenticated user should be restricted from internal pages."""
        pages = ["/dashboard", "/apply", "/predict", "/history", "/models", "/admin"]
        for page in pages:
            res = self.client.get(page)
            self.assertEqual(res.status_code, 302, f"Failed for {page}")
            self.assertIn("/login", res.location)

    def test_authorization_non_admin_blocked(self):
        """A standard user must be blocked from admin features (403 Forbidden)."""
        # Register and log in a regular user
        self.client.post("/register", data={
            "name": "Regular User",
            "email": "test_regular@test.com",
            "password": "user_password",
            "confirm_password": "user_password"
        })
        self.client.post("/login", data={
            "email": "test_regular@test.com",
            "password": "user_password"
        })

        admin_pages = ["/admin", "/admin/users", "/admin/applicants", "/admin/predictions", "/admin/export/users"]
        for page in admin_pages:
            res = self.client.get(page)
            # The app returns 403 Forbidden via @admin_required
            self.assertEqual(res.status_code, 403, f"Non-admin wasn't blocked from {page}")

    def test_apply_and_predict_flow(self):
        """Complete application submission and prediction flow."""
        # 1. Register and log in standard user
        self.client.post("/register", data={
            "name": "Applicant Tester",
            "email": "test_applicant@test.com",
            "password": "user_password",
            "confirm_password": "user_password"
        })
        self.client.post("/login", data={
            "email": "test_applicant@test.com",
            "password": "user_password"
        })

        # 2. Submit applicant form
        form_data = {
            "full_name": "Test Applicant",
            "age": "25",
            "gender": "Female",
            "annual_income": "54000.00",
            "income_type": "Working",
            "education_type": "Higher education",
            "family_status": "Single / not married",
            "housing_type": "Rented apartment",
            "employment_days": "1200",
            "family_member_count": "1",
            "owns_car": "on",
            "owns_property": "off",
            "num_children": "0",
            "work_phone_provided": "off",
            "phone_provided": "on",
            "email_provided": "on",
            "months_balance": "-12",
            "overdue_months": "0",
            "payment_status": "C"
        }
        res = self.client.post("/apply", data=form_data, follow_redirects=True)
        # Should redirect to predict page animation
        self.assertIn(b"AI Model Processing", res.data)

        # 3. Post to predict to trigger execution
        res_predict = self.client.post("/predict", follow_redirects=True)
        self.assertEqual(res_predict.status_code, 200)
        # Verify prediction result page is shown
        self.assertIn(b"Prediction Result", res_predict.data)
        self.assertTrue(b"Approved" in res_predict.data or b"Rejected" in res_predict.data)

    def test_admin_dashboard_and_exports(self):
        """Admin user dashboard access and CSV exports."""
        # Log in default admin
        res = self.client.post("/login", data={
            "email": "admin@creditcard.com",
            "password": "Admin@1234"
        }, follow_redirects=True)
        self.assertIn(b"Admin Panel", res.data)

        # Export users CSV
        res_export_users = self.client.get("/admin/export/users")
        self.assertEqual(res_export_users.status_code, 200)
        self.assertEqual(res_export_users.mimetype, "text/csv")
        self.assertIn(b"UserID,Name,Email,Role,CreatedAt", res_export_users.data)

        # Export predictions CSV
        res_export_preds = self.client.get("/admin/export/predictions")
        self.assertEqual(res_export_preds.status_code, 200)
        self.assertEqual(res_export_preds.mimetype, "text/csv")
        self.assertIn(b"PredictionID,FullName,Email,", res_export_preds.data)

    def test_ajax_apply_and_predict_flow(self):
        """Test AJAX submission for applicant form and prediction request."""
        # 1. Register and log in standard user
        self.client.post("/register", data={
            "name": "AJAX Tester",
            "email": "test_ajax@test.com",
            "password": "user_password",
            "confirm_password": "user_password"
        })
        self.client.post("/login", data={
            "email": "test_ajax@test.com",
            "password": "user_password"
        })

        # 2. Submit form via AJAX
        form_data = {
            "full_name": "AJAX Applicant",
            "age": "30",
            "gender": "Male",
            "annual_income": "85000.00",
            "income_type": "State servant",
            "education_type": "Academic degree",
            "family_status": "Married",
            "housing_type": "House / apartment",
            "employment_days": "3650",
            "family_member_count": "2",
            "owns_car": "off",
            "owns_property": "on",
            "num_children": "0",
            "work_phone_provided": "on",
            "phone_provided": "on",
            "email_provided": "on",
            "months_balance": "-6",
            "overdue_months": "0",
            "payment_status": "C"
        }
        res = self.client.post("/apply", data=form_data, headers={"X-Requested-With": "XMLHttpRequest"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, "application/json")
        json_data = res.get_json()
        self.assertTrue(json_data.get("success"))
        self.assertIn("applicant_id", json_data)

        # 3. Request prediction via AJAX
        res_predict = self.client.post("/predict", headers={"X-Requested-With": "XMLHttpRequest"})
        self.assertEqual(res_predict.status_code, 200)
        self.assertEqual(res_predict.mimetype, "application/json")
        pred_json = res_predict.get_json()
        self.assertTrue(pred_json.get("success"))
        self.assertIn("prediction_id", pred_json)
        self.assertIn(pred_json.get("result"), ["Approved", "Rejected"])
        self.assertIn("confidence", pred_json)
        self.assertIn("risk", pred_json)
        self.assertEqual(pred_json.get("name"), "AJAX Applicant")

    def test_sandbox_and_simulator_api(self):
        """Test sandbox rendering and simulated API predictions."""
        # 1. Register and log in standard user
        self.client.post("/register", data={
            "name": "Sandbox Tester",
            "email": "test_sandbox@test.com",
            "password": "user_password",
            "confirm_password": "user_password"
        })
        self.client.post("/login", data={
            "email": "test_sandbox@test.com",
            "password": "user_password"
        })

        # 2. View Sandbox page
        res = self.client.get("/sandbox")
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Interactive \"What-If\" Credit Simulator", res.data)

        # 3. Trigger simulation prediction API
        data = {
            "annual_income": "600000",
            "overdue_months": "0",
            "employment_days": "1825",
            "age": "35",
            "education_type": "Higher education",
            "housing_type": "House / apartment",
            "owns_property": "on",
            "owns_car": "off"
        }
        res_api = self.client.post("/api/predict/sandbox", json=data)
        self.assertEqual(res_api.status_code, 200)
        self.assertEqual(res_api.mimetype, "application/json")
        res_json = res_api.get_json()
        self.assertTrue(res_json.get("success"))
        self.assertIn("result", res_json)
        self.assertIn("confidence", res_json)
        self.assertIn("impacts", res_json)
        
        # Verify XAI feature list has calculated impacts
        impacts = res_json.get("impacts")
        self.assertTrue(len(impacts) > 0)
        self.assertEqual(impacts[0].get("name"), "Annual Income")

if __name__ == "__main__":
    unittest.main()
