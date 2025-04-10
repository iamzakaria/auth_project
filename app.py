from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
import re
from werkzeug.security import generate_password_hash, check_password_hash
from contextlib import contextmanager

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Database connection
@contextmanager
def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",  # Replace with your MySQL username
        password="root",  # Replace with your MySQL password
        database="user_auth"
    )
    try:
        yield conn
    finally:
        conn.close()

# Validation Functions
def validate_name(name, field):
    if not name or not re.match(r"^[a-zA-Z\s]{2,50}$", name):
        flash(f"{field} must be 2-50 letters only.", "danger")
        return False
    return True

def validate_email(email):
    if not email or not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
        flash("Please enter a valid email address.", "danger")
        return False
    return True

def validate_password(password):
    if not re.match(r"^(?=.*[0-9])(?=.*[!@#$%^&*])[a-zA-Z0-9!@#$%^&*]{8,}$", password):
        flash("Password must be 8+ chars with at least 1 number and 1 special char.", "danger")
        return False
    return True

def validate_age(age):
    try:
        age = int(age)
        if age < 18 or age > 120:
            flash("Age must be between 18 and 120.", "danger")
            return False
        return age
    except ValueError:
        flash("Age must be a number.", "danger")
        return False

def validate_gender(gender):
    valid_genders = ["Male", "Female", "Other"]
    if gender not in valid_genders:
        flash("Gender must be Male, Female, or Other.", "danger")
        return False
    return True

def validate_designation(designation):
    if not designation or len(designation) > 100:
        flash("Designation must be 1-100 characters.", "danger")
        return False
    return True

# Routes
@app.route('/')
def index():
    return render_template('landing.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        firstname = request.form['firstname'].strip()
        lastname = request.form['lastname'].strip()
        email = request.form['email'].strip()
        password = request.form['password'].strip()
        confirm_password = request.form['confirm_password'].strip()
        gender = request.form['gender'].strip()
        designation = request.form['designation'].strip()
        age = request.form['age'].strip()

        # Validation
        if not all([
            validate_name(firstname, "First Name"),
            validate_name(lastname, "Last Name"),
            validate_email(email),
            validate_password(password),
            validate_gender(gender),
            validate_designation(designation)
        ]):
            return render_template('register.html')

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return render_template('register.html')

        age = validate_age(age)
        if not age:
            return render_template('register.html')

        # Store in DB with hashed password
        try:
            with get_db_connection() as db:
                cursor = db.cursor()
                # Check if email already exists
                cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash("Email already registered", "danger")
                    return render_template('register.html')
                
                # Hash password before storing
                hashed_password = generate_password_hash(password)
                query = """
                    INSERT INTO users (firstname, lastname, email, password, gender, designation, age)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (firstname, lastname, email, hashed_password, gender, designation, age))
                db.commit()
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f"Database error occurred. Please try again.", "danger")

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip()
        password = request.form['password'].strip()

        print(f"Login attempt - Email: {email}, Password: {password}")

        try:
            with get_db_connection() as db:
                cursor = db.cursor()
                query = "SELECT firstname, lastname, password FROM users WHERE email = %s"
                cursor.execute(query, (email,))
                result = cursor.fetchone()

                if result:
                    firstname, lastname, stored_password = result
                    if check_password_hash(stored_password, password):
                        session['email'] = email
                        session['firstname'] = firstname
                        session['lastname'] = lastname
                        flash("Login successful!", "success")
                        return redirect(url_for('dashboard'))
                    else:
                        flash("Invalid password.", "danger")
                else:
                    flash("User not found. Please check your email or <a href='/register'>register now</a>.", "danger")
        except mysql.connector.Error as err:
            flash("An error occurred during login. Please try again.", "danger")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('login'))
    firstname = session.get('firstname', 'User')
    lastname = session.get('lastname', '')
    return render_template('dashboard.html', firstname=firstname, lastname=lastname)

@app.route('/logout')
def logout():
    session.pop('email', None)
    session.pop('firstname', None)
    session.pop('lastname', None)
    flash("Logged out successfully.", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)