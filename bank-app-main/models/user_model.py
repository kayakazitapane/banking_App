import os
import hashlib
import uuid
from datetime import datetime

class UserModel:
    db_path = "database/users.txt"

    @staticmethod
    def hash_password(password):
        """Hash the password using SHA256."""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def ensure_database_exists():
        """Ensure the main user database file exists."""
        if not os.path.exists(UserModel.db_path):
            os.makedirs(os.path.dirname(UserModel.db_path), exist_ok=True)
            with open(UserModel.db_path, "w") as file:
                pass  # Create an empty file

    @staticmethod
    def generate_account_number():
        """Generate a unique 10-digit account number."""
        return str(uuid.uuid4().int)[:10]

    @staticmethod
    def save_user(name, surname, phone, id_number, email, username, password):
        """Save user details to the database file with an account number."""
        UserModel.ensure_database_exists()
        try:
            account_number = UserModel.generate_account_number()
            with open(UserModel.db_path, "a") as file:
                # Default balance is set to 0.0
                file.write(
                    f"{account_number},{name},{surname},{phone},{id_number},{email},{username},{UserModel.hash_password(password)},0.0\n")
            # Create a default "Savings" account for the new user
            UserModel.add_account(username, "Savings", 0.0)
        except Exception as e:
            print(f"Error saving user: {e}")

    @staticmethod
    def get_user(username):
        """Retrieve a user's details by username."""
        UserModel.ensure_database_exists()
        try:
            with open(UserModel.db_path, "r") as file:
                for line in file:
                    data = line.strip().split(",")
                    if data[6] == username:  # Username is now the 7th field
                        return {
                            "account_number": data[0],
                            "name": data[1],
                            "surname": data[2],
                            "phone": data[3],
                            "id_number": data[4],
                            "email": data[5],
                            "username": data[6],
                            "password_hash": data[7],
                            "balance": float(data[8]),  # Balance is the last field
                        }
        except Exception as e:
            print(f"Error retrieving user: {e}")
        return None

    @staticmethod
    def update_balance(username, new_balance):
        """Update the user's balance in the main database."""
        UserModel.ensure_database_exists()
        lines = []
        try:
            with open(UserModel.db_path, "r") as file:
                for line in file:
                    data = line.strip().split(",")
                    if data[6] == username:  # Username is the 7th field
                        data[8] = str(new_balance)  # Update balance (9th field)
                    lines.append(",".join(data))

            with open(UserModel.db_path, "w") as file:
                for line in lines:
                    file.write(line + "\n")
        except Exception as e:
            print(f"Error updating balance: {e}")

    @staticmethod
    def update_user(username, updates):
        """Update specific fields for a user."""
        UserModel.ensure_database_exists()
        lines = []
        try:
            with open(UserModel.db_path, "r") as file:
                for line in file:
                    data = line.strip().split(",")
                    if data[6] == username:  # Username is the 7th field
                        data = [
                            updates.get("name", data[0]),
                            data[1],  # Surname remains the same
                            data[2],  # Phone remains the same
                            data[3],  # ID number remains the same
                            data[4],  # Email remains the same
                            data[5],  # Username remains the same
                            updates.get("password_hash", data[6]),  # Update password hash if provided
                            data[7],  # Balance remains the same
                        ]
                    lines.append(",".join(data))

            with open(UserModel.db_path, "w") as file:
                for line in lines:
                    file.write(line + "\n")
        except Exception as e:
            print(f"Error updating user: {e}")

    @staticmethod
    def get_accounts(username):
        """Fetch all accounts for the user."""
        accounts_file = f"database/{username}_accounts.txt"
        if not os.path.exists(accounts_file):
            return []  # No accounts yet

        accounts = []
        try:
            with open(accounts_file, "r") as file:
                for line in file:
                    try:
                        name, balance = line.strip().split(",")
                        accounts.append({"name": name, "balance": float(balance)})
                    except ValueError:
                        print(f"Skipping malformed line in {accounts_file}: {line}")
        except Exception as e:
            print(f"Error reading accounts file for {username}: {e}")
        return accounts

    @staticmethod
    def add_account(username, account_name, initial_balance):
        """Add a new account for the user and deduct from main balance."""
        if initial_balance < 0:
            print(f"Cannot add account with negative balance: {initial_balance}")
            return False

        user = UserModel.get_user(username)
        if not user:
            print(f"User {username} not found.")
            return False

        # Check if the user has sufficient funds
        if user["balance"] < initial_balance:
            print(f"Insufficient funds in main account to create {account_name}.")
            return False

        accounts_file = f"database/{username}_accounts.txt"
        existing_accounts = UserModel.get_accounts(username)

        # Check for duplicate account names
        if any(account["name"] == account_name for account in existing_accounts):
            print(f"Account with name '{account_name}' already exists for user '{username}'.")
            return False

        try:
            # Deduct initial balance from main account
            UserModel.update_balance(username, user["balance"] - initial_balance)

            # Add the new account
            with open(accounts_file, "a") as file:
                file.write(f"{account_name},{initial_balance}\n")

            # Log the transaction
            UserModel.log_transaction(
                username,
                "Account Creation",
                initial_balance,
                f"Created account '{account_name}'",
                user["balance"] - initial_balance
            )

            return True  # Indicate success
        except Exception as e:
            print(f"Error adding account for {username}: {e}")
            return False

    @staticmethod
    def get_total_balance(username):
        """Calculate the total balance across all accounts."""
        accounts = UserModel.get_accounts(username)
        return sum(account["balance"] for account in accounts)

    @staticmethod
    def log_transaction(username, transaction_type, amount, details="", balance_after=None):
        """Log a transaction for the user."""
        transaction_file = f"database/{username}_transactions.txt"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(transaction_file, "a") as file:
                file.write(f"{timestamp},{transaction_type},{amount},{details},{balance_after}\n")
        except Exception as e:
            print(f"Error logging transaction for {username}: {e}")

    @staticmethod
    def get_transaction_history(username):
        """Fetch transaction history for the user."""
        transaction_file = f"database/{username}_transactions.txt"
        if not os.path.exists(transaction_file):
            return []  # No transactions yet

        transactions = []
        try:
            with open(transaction_file, "r") as file:
                for line in file:
                    try:
                        timestamp, transaction_type, amount, details, balance_after = line.strip().split(",", 4)
                        transactions.append({
                            "timestamp": timestamp,
                            "type": transaction_type,
                            "amount": float(amount),
                            "details": details,
                            "balance_after": float(balance_after)
                        })
                    except ValueError:
                        print(f"Skipping malformed transaction line: {line}")
        except Exception as e:
            print(f"Error reading transactions for {username}: {e}")
        return transactions