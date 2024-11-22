import re
from flask import render_template, request, redirect, flash, session
from models.user_model import UserModel


class AuthController:
    @staticmethod
    def validate_email(email):
        """Validate email format."""
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(email_regex, email)

    @staticmethod
    def validate_password(password):
        """Check for strong password: min 8 chars, uppercase, lowercase, number, special char."""
        if len(password) < 8:
            return "Password must be at least 8 characters long."
        if not re.search(r'[A-Z]', password):
            return "Password must include at least one uppercase letter."
        if not re.search(r'[a-z]', password):
            return "Password must include at least one lowercase letter."
        if not re.search(r'\d', password):
            return "Password must include at least one number."
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return "Password must include at least one special character."
        return None

    @staticmethod
    def register():
        """Handle user registration."""
        if request.method == "POST":
            name = request.form.get("name")
            surname = request.form.get("surname")
            phone = request.form.get("phone")
            id_number = request.form.get("id_number")
            email = request.form.get("email")
            username = request.form.get("username")
            password = request.form.get("password")
            confirm_password = request.form.get("confirm_password")

            # Collect errors
            errors = []

            # Validate email
            if not AuthController.validate_email(email):
                errors.append("Invalid email format.")

            # Validate password strength
            password_error = AuthController.validate_password(password)
            if password_error:
                errors.append(password_error)

            # Confirm password
            if password != confirm_password:
                errors.append("Passwords do not match.")

            # Check if username already exists
            if UserModel.get_user(username):
                errors.append("Username already exists. Please choose another.")

            # If there are errors, flash them and reload the form
            if errors:
                for error in errors:
                    flash(error)
                return render_template("register.html")

            # Save user
            UserModel.save_user(name, surname, phone, id_number, email, username, password)
            flash("Registration successful! Please log in.")
            return redirect("/login")

        return render_template("register.html")

    @staticmethod
    def login():
        """Handle user login."""
        if request.method == "POST":
            username = request.form.get("username")
            password = request.form.get("password")

            # Fetch user details
            user = UserModel.get_user(username)
            if user and user["password_hash"] == UserModel.hash_password(password):  # Password match
                session["user"] = {
                    "name": user["name"],
                    "surname": user["surname"],
                    "email": user["email"],
                    "username": user["username"],
                }
                flash(f"Welcome, {user['name']}!")
                return redirect("/dashboard")
            else:
                flash("Invalid username or password.")
                return render_template("login.html", username=username)

        return render_template("login.html")

    @staticmethod
    def logout():
        """Handle user logout."""
        session.clear()
        flash("You have been logged out.")
        return redirect("/login")
