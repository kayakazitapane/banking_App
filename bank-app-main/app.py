from flask import Flask, render_template, request, redirect, url_for, flash
from controllers.auth_controller import AuthController
from flask import session
from models.user_model import UserModel
import csv
from flask import make_response

app = Flask(__name__)
app.secret_key = "your_secret_key"  # For flash messages

# Routes
@app.route("/")
def home():
    return redirect(url_for("login"))

## Register
@app.route("/register", methods=["GET", "POST"])
def register():
    return AuthController.register()


@app.route("/login", methods=["GET", "POST"])
def login():
    return AuthController.login()


@app.route("/logout")
def logout():
    return AuthController.logout()


@app.route("/dashboard")
def dashboard():
    # Check if the user is logged in
    if "user" not in session:
        flash("Please log in to access the dashboard.")
        return redirect("/login")

    # Fetch the full user details
    user = UserModel.get_user(session["user"]["username"])
    if not user:
        flash("User not found. Please log in again.")
        return redirect("/logout")  # Redirect to logout to clear session

    return render_template("dashboard.html", user=user)



@app.route("/deposit", methods=["GET", "POST"])
def deposit():
    if "user" not in session:
        flash("Please log in to access this feature.")
        return redirect("/login")

    if request.method == "POST":
        amount = request.form.get("amount", type=float)
        if amount <= 0:
            flash("Deposit amount must be greater than 0.")
            return render_template("deposit.html")

        user = session["user"]
        current_balance = UserModel.get_user(user["username"])["balance"]
        new_balance = current_balance + amount
        UserModel.update_balance(user["username"], new_balance)

        # Log the transaction
        UserModel.log_transaction(user["username"], "Deposit", amount, "Deposit to main account", new_balance)

        flash(f"Successfully deposited ${amount:.2f}.")
        return redirect("/dashboard")

    return render_template("deposit.html")



@app.route("/withdraw", methods=["GET", "POST"])
def withdraw():
    if "user" not in session:
        flash("Please log in to access this feature.")
        return redirect("/login")

    if request.method == "POST":
        amount = request.form.get("amount", type=float)
        user = session["user"]
        current_balance = UserModel.get_user(user["username"])["balance"]

        if amount <= 0:
            flash("Withdrawal amount must be greater than 0.")
            return render_template("withdraw.html")

        if amount > current_balance:
            flash("Insufficient funds.")
            return render_template("withdraw.html")

        new_balance = current_balance - amount
        UserModel.update_balance(user["username"], new_balance)

        # Log the transaction
        UserModel.log_transaction(user["username"], "Withdrawal", amount, "Withdrawal from main account", new_balance)

        flash(f"Successfully withdrew ${amount:.2f}.")
        return redirect("/dashboard")

    return render_template("withdraw.html")



@app.route("/transfer", methods=["GET", "POST"])
def transfer():
    if "user" not in session:
        flash("Please log in to access this feature.")
        return redirect("/login")

    if request.method == "POST":
        recipient_username = request.form.get("recipient_username")
        amount = request.form.get("amount", type=float)

        if amount <= 0:
            flash("Transfer amount must be greater than 0.")
            return render_template("transfer.html")

        user = session["user"]
        current_balance = UserModel.get_user(user["username"])["balance"]

        if amount > current_balance:
            flash("Insufficient funds.")
            return render_template("transfer.html")

        recipient = UserModel.get_user(recipient_username)
        if not recipient:
            flash("Recipient username does not exist.")
            return render_template("transfer.html")

        # Update balances
        UserModel.update_balance(user["username"], current_balance - amount)
        UserModel.update_balance(recipient_username, recipient["balance"] + amount)

        flash(f"Successfully transferred ${amount:.2f} to {recipient_username}.")
        return redirect("/dashboard")

    return render_template("transfer.html")


@app.route("/send_money", methods=["GET", "POST"])
def send_money():
    if "user" not in session:
        flash("Please log in to access this feature.")
        return redirect("/login")

    if request.method == "POST":
        external_account = request.form.get("external_account")
        amount = request.form.get("amount", type=float)
        transaction_fee = 2.5  # Flat transaction fee for external transfers

        if amount <= 0:
            flash("Transfer amount must be greater than 0.")
            return render_template("send_money.html")

        user = session["user"]
        current_balance = UserModel.get_user(user["username"])["balance"]

        if amount + transaction_fee > current_balance:
            flash("Insufficient funds for this transfer.")
            return render_template("send_money.html")

        # Deduct amount + fee from the user's account
        new_balance = current_balance - (amount + transaction_fee)
        UserModel.update_balance(user["username"], new_balance)

        flash(
            f"Successfully transferred ${amount:.2f} to external account '{external_account}' with a ${transaction_fee:.2f} fee.")
        return redirect("/dashboard")

    return render_template("send_money.html")


@app.route("/accounts", methods=["GET", "POST"])
def accounts():
    if "user" not in session:
        flash("Please log in to access this feature.")
        return redirect("/login")

    user = session["user"]
    accounts = UserModel.get_accounts(user["username"])  # Fetch all accounts for the user

    return render_template("accounts.html", accounts=accounts)


@app.route("/create_account", methods=["GET", "POST"])
def create_account():
    if "user" not in session:
        flash("Please log in to access this feature.")
        return redirect("/login")

    if request.method == "POST":
        account_name = request.form.get("account_name")
        initial_balance = request.form.get("initial_balance", type=float)
        user = session["user"]

        if initial_balance < 0:
            flash("Initial balance cannot be negative.")
            return render_template("create_account.html")

        UserModel.add_account(user["username"], account_name, initial_balance)
        flash(f"Account '{account_name}' created successfully with an initial balance of ${initial_balance:.2f}.")
        return redirect("/accounts")

    return render_template("create_account.html")


@app.route("/transactions", methods=["GET", "POST"])
def transactions():
    if "user" not in session:
        flash("Please log in to access this feature.")
        return redirect("/login")

    user = session["user"]
    transactions = UserModel.get_transaction_history(user["username"])

    # Handle filtering
    if request.method == "POST":
        transaction_type = request.form.get("transaction_type")
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        # Filter by transaction type
        if transaction_type and transaction_type != "All":
            transactions = [txn for txn in transactions if txn["type"] == transaction_type]

        # Filter by date range
        if start_date:
            transactions = [txn for txn in transactions if txn["timestamp"] >= start_date]
        if end_date:
            transactions = [txn for txn in transactions if txn["timestamp"] <= end_date]

    return render_template("transactions.html", transactions=transactions)




@app.route("/export_transactions")
def export_transactions():
    if "user" not in session:
        flash("Please log in to access this feature.")
        return redirect("/login")

    user = session["user"]
    transactions = UserModel.get_transaction_history(user["username"])

    # Create a CSV response
    csv_data = [["Date", "Type", "Amount", "Details", "Balance After"]]
    for txn in transactions:
        csv_data.append([txn["timestamp"], txn["type"], txn["amount"], txn["details"], txn["balance_after"]])

    # Generate CSV file as response
    response = make_response("\n".join([",".join(map(str, row)) for row in csv_data]))
    response.headers["Content-Disposition"] = "attachment; filename=transactions.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


if __name__ == "__main__":
    app.run(debug=True)