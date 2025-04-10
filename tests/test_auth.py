import pytest
from playwright.sync_api import Page, expect
from faker import Faker

@pytest.fixture(scope="function")
def test_page(page: Page):
    # Navigate to the base URL before each test
    page.goto("http://127.0.0.1:5000")
    page.wait_for_load_state("networkidle")
    return page

@pytest.fixture(scope="function")
def test_user():
    """Generate random user data for testing"""
    fake = Faker()
    password = f"{fake.word().capitalize()}@{fake.random_number(digits=3)}"
    return {
        "firstname": fake.first_name(),
        "lastname": fake.last_name(),
        "email": fake.email(),
        "password": password,
        "confirm_password": password
    }

class TestAuthentication:
    def test_login_page_elements(self, test_page):
        """Test the presence of all login page elements"""
        test_page.goto("http://127.0.0.1:5000/login")
        test_page.wait_for_load_state("networkidle")
        # Check form elements
        expect(test_page.get_by_label("Email Address")).to_be_visible()
        expect(test_page.get_by_label("Password")).to_be_visible()
        expect(test_page.get_by_role("button", name="Sign In")).to_be_visible()
        expect(test_page.get_by_role("link", name="Don't have an account? Register")).to_be_visible()

    def test_register_page_elements(self, test_page):
        """Test the presence of all registration page elements"""
        test_page.goto("http://127.0.0.1:5000/register")
        # Check form elements
        expect(test_page.get_by_label("First Name")).to_be_visible()
        expect(test_page.get_by_label("Last Name")).to_be_visible()
        expect(test_page.get_by_label("Email Address")).to_be_visible()
        expect(test_page.get_by_label("Password")).to_be_visible()
        expect(test_page.get_by_label("Confirm Password")).to_be_visible()
        expect(test_page.get_by_role("button", name="Register")).to_be_visible()

    def test_invalid_email_validation(self, test_page):
        """Test email validation on login form"""
        test_page.goto("http://127.0.0.1:5000/login")
        email_input = test_page.get_by_label("Email Address")
        # Test invalid email format
        email_input.fill("invalid-email")
        email_input.blur()
        expect(test_page.locator(".invalid-feedback")).to_contain_text("Please enter a valid email address")

    def test_password_visibility_toggle(self, test_page):
        """Test password visibility toggle functionality"""
        test_page.goto("http://127.0.0.1:5000/login")
        password_input = test_page.get_by_label("Password")
        toggle_button = test_page.get_by_role("button", name="Toggle password visibility")
        
        # Initial state should be password
        expect(password_input).to_have_attribute("type", "password")
        # Click toggle button
        toggle_button.click()
        # Should show password
        expect(password_input).to_have_attribute("type", "text")
        # Click again
        toggle_button.click()
        # Should hide password
        expect(password_input).to_have_attribute("type", "password")

    def test_successful_registration(self, test_page, test_user):
        """Test successful user registration"""
        test_page.goto("http://127.0.0.1:5000/register")
        test_page.wait_for_load_state("networkidle")
        # Fill registration form
        test_page.get_by_label("First Name").fill(test_user["firstname"])
        test_page.get_by_label("Last Name").fill(test_user["lastname"])
        test_page.get_by_label("Email Address").fill(test_user["email"])
        test_page.get_by_label("Password").fill(test_user["password"])
        test_page.get_by_label("Confirm Password").fill(test_user["confirm_password"])
        
        # Submit form
        test_page.get_by_role("button", name="Register").click()
        test_page.wait_for_timeout(1000)  # Wait for form submission and response
        # Check for success message
        expect(test_page.locator(".alert-success")).to_be_visible()

    def test_successful_login(self, test_page, test_user):
        """Test successful login with valid credentials"""
        # First register the user
        self.test_successful_registration(test_page, test_user)
        
        test_page.goto("http://127.0.0.1:5000/login")
        test_page.wait_for_load_state("networkidle")
        # Fill login form
        test_page.get_by_label("Email Address").fill(test_user["email"])
        test_page.get_by_label("Password").fill(test_user["password"])
        
        # Submit form
        test_page.get_by_role("button", name="Sign In").click()
        test_page.wait_for_timeout(1000)  # Wait for form submission and response
        # Check if redirected to dashboard
        expect(test_page).to_have_url("http://127.0.0.1:5000/dashboard")
        expect(test_page.get_by_text(f"Welcome, {test_user['firstname']} {test_user['lastname']}!")).to_be_visible()

    def test_invalid_login(self, test_page):
        """Test login with invalid credentials"""
        test_page.goto("http://127.0.0.1:5000/login")
        
        # Test with non-existent user
        test_page.get_by_label("Email Address").fill("nonexistent@example.com")
        test_page.get_by_label("Password").fill("ValidPass@123")
        test_page.get_by_role("button", name="Sign In").click()
        expect(test_page.locator(".alert-danger")).to_contain_text("User not found")
        
        # Test with wrong password for existing user
        test_user = {
            "firstname": "Test",
            "lastname": "User",
            "email": "test@example.com",
            "password": "TestPass@123",
            "confirm_password": "TestPass@123"
        }
        # Register the test user first
        test_page.goto("http://127.0.0.1:5000/register")
        test_page.get_by_label("First Name").fill(test_user["firstname"])
        test_page.get_by_label("Last Name").fill(test_user["lastname"])
        test_page.get_by_label("Email Address").fill(test_user["email"])
        test_page.get_by_label("Password").fill(test_user["password"])
        test_page.get_by_label("Confirm Password").fill(test_user["confirm_password"])
        test_page.get_by_role("button", name="Register").click()
        test_page.wait_for_timeout(1000)
        
        # Try to login with wrong password
        test_page.goto("http://127.0.0.1:5000/login")
        test_page.get_by_label("Email Address").fill(test_user["email"])
        test_page.get_by_label("Password").fill("WrongPass@123")
        test_page.get_by_role("button", name="Sign In").click()
        expect(test_page.locator(".alert-danger")).to_contain_text("Invalid password")
        
        # Fill login form with invalid credentials
        test_page.get_by_label("Email Address").fill("wrong@example.com")
        test_page.get_by_label("Password").fill("WrongPass@123")
        
        # Submit form
        test_page.get_by_role("button", name="Sign In").click()
        # Check for error message
        expect(test_page.locator(".alert-danger")).to_be_visible()

    def test_password_validation(self, test_page):
        """Test password validation rules during registration"""
        test_page.goto("http://127.0.0.1:5000/register")
        password_input = test_page.get_by_label("Password")
        
        # Test password without special character
        password_input.fill("Password123")
        password_input.blur()
        expect(test_page.locator(".invalid-feedback")).to_be_visible()
        
        # Test password without number
        password_input.fill("Password@")
        password_input.blur()
        expect(test_page.locator(".invalid-feedback")).to_be_visible()
        
        # Test password too short
        password_input.fill("P@1")
        password_input.blur()
        expect(test_page.locator(".invalid-feedback")).to_be_visible()

    def test_logout(self, test_page, test_user):
        """Test logout functionality"""
        # First login with the test user
        self.test_successful_login(test_page, test_user)
        
        # Click logout
        test_page.get_by_role("link", name="Logout").click()
        test_page.wait_for_timeout(1000)  # Wait for logout process
        # Verify redirect to login page
        expect(test_page).to_have_url("http://127.0.0.1:5000/login")
        # Verify success message
        expect(test_page.locator(".alert-success")).to_contain_text("You have been logged out successfully")