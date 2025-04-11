from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from web3 import Web3
import json
from datetime import datetime
import uuid

# App configuration
app = Flask(__name__)
app.config["SECRET_KEY"] = "your_secret_key_here"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///landregistry.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"] = "static/uploads"
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload size

# Ensure upload directories exist
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "profiles"), exist_ok=True)
os.makedirs(os.path.join(app.config["UPLOAD_FOLDER"], "lands"), exist_ok=True)

# Initialize database
db = SQLAlchemy(app)

# Web3 configuration - connect to local blockchain
w3 = Web3(
    Web3.HTTPProvider("http://127.0.0.1:8545")
)  # Change to your blockchain endpoint

# Load smart contract ABI and address
# with open("contract_abi.json", "r") as f:
#     contract_abi = json.load(f)

# contract_address = (
#     "0xYourContractAddressHere"  # Replace with your deployed contract address
# )
# land_registry_contract = w3.eth.contract(address=contract_address, abi=contract_abi)


# Database models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    blockchain_address = db.Column(db.String(42), unique=True, nullable=False)
    profile_image = db.Column(db.String(200), default="default_profile.jpg")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User {self.username}>"


class Land(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blockchain_id = db.Column(db.Integer, unique=True, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200))
    for_sale = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owner = db.relationship("User", backref=db.backref("lands", lazy=True))

    def __repr__(self):
        return f"<Land {self.title}>"


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    blockchain_tx_hash = db.Column(db.String(66), unique=True, nullable=False)
    land_id = db.Column(db.Integer, db.ForeignKey("land.id"), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    price = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)

    land = db.relationship("Land", backref=db.backref("transactions", lazy=True))
    seller = db.relationship("User", foreign_keys=[seller_id])
    buyer = db.relationship("User", foreign_keys=[buyer_id])

    def __repr__(self):
        return f"<Transaction {self.blockchain_tx_hash[:10]}>"


# Helper functions
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_file(file, folder):
    if file and allowed_file(file.filename):
        filename = str(uuid.uuid4()) + "." + file.filename.rsplit(".", 1)[1].lower()
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], folder, filename)
        file.save(file_path)
        return os.path.join(folder, filename)
    return None


# Routes
@app.route("/")
def index():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        # Form validation
        if User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
            return redirect(url_for("register"))

        if User.query.filter_by(email=email).first():
            flash("Email already registered", "danger")
            return redirect(url_for("register"))

        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for("register"))

        # Generate blockchain wallet
        wallet = w3.eth.account.create()

        # Assign default profile image
        profile_image = "default_profile.jpg"

        # Create user in database
        new_user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            blockchain_address=wallet.address,
            profile_image=profile_image,
        )

        try:
            db.session.add(new_user)
            db.session.commit()

            flash("Registration successful! You can now log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            session["username"] = user.username
            session["blockchain_address"] = user.blockchain_address

            flash("Login successful!", "success")
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])
    user_lands = Land.query.filter_by(owner_id=user.id).all()

    return render_template("dashboard.html", user=user, lands=user_lands)


@app.route("/profile", methods=["GET", "POST"])
def profile():
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    user = User.query.get(session["user_id"])

    if request.method == "POST":
        if "profile_image" in request.files:
            file = request.files["profile_image"]
            if file.filename:
                saved_path = save_file(file, "profiles")
                if saved_path:
                    user.profile_image = saved_path
                    db.session.commit()
                    flash("Profile image updated successfully", "success")

        return redirect(url_for("profile"))

    return render_template("profile.html", user=user)


@app.route("/registerLand", methods=["GET", "POST"])
def registerLand():
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        location = request.form["location"]
        description = request.form["description"]
        price = float(request.form["price"])
        for_sale = "for_sale" in request.form

        # Save land image
        land_image = "default_land.png"
        if "land_image" in request.files:
            file = request.files["land_image"]
            if file.filename:
                saved_path = save_file(file, "lands")
                if saved_path:
                    land_image = saved_path

        # Create land on blockchain
        try:
            # This would be the actual blockchain transaction in production
            # For demonstration, we'll simulate by creating a local record

            # Create local record
            new_land = Land(
                blockchain_id=Land.query.count() + 1,  # Simulated blockchain ID
                owner_id=session["user_id"],
                title=title,
                location=location,
                description=description,
                price=price,
                image=land_image,
                for_sale=for_sale,
            )

            db.session.add(new_land)
            db.session.commit()

            flash("Land registered successfully!", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")

    return render_template("registerLand.html")


@app.route("/marketplace")
def marketplace():
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    lands_for_sale = Land.query.filter_by(for_sale=True).all()
    return render_template("marketplace.html", lands=lands_for_sale)


@app.route("/land/<int:land_id>")
def landDetails(land_id):
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    land = Land.query.get_or_404(land_id)
    return render_template("landDetails.html", land=land)


@app.route("/buy_land/<int:land_id>", methods=["POST"])
def buy_land(land_id):
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    land = Land.query.get_or_404(land_id)
    buyer_id = session["user_id"]

    if land.owner_id == buyer_id:
        flash("You already own this land", "warning")
        return redirect(url_for("landDetails", land_id=land_id))

    if not land.for_sale:
        flash("This land is not for sale", "warning")
        return redirect(url_for("landDetails", land_id=land_id))

    try:
        # In a real application, this would involve a blockchain transaction
        # For demonstration, we'll simulate the transaction

        # Record the transaction
        transaction = Transaction(
            blockchain_tx_hash=f"0x{os.urandom(32).hex()}",  # Simulated transaction hash
            land_id=land.id,
            seller_id=land.owner_id,
            buyer_id=buyer_id,
            price=land.price,
        )

        # Transfer ownership
        land.owner_id = buyer_id
        land.for_sale = False

        db.session.add(transaction)
        db.session.commit()

        flash("Land purchased successfully!", "success")
        return redirect(url_for("dashboard"))
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")
        return redirect(url_for("landDetails", land_id=land_id))


@app.route("/transactions")
def transaction_history():
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    user_id = session["user_id"]

    # Get transactions where user is either buyer or seller
    transactions = (
        Transaction.query.filter(
            (Transaction.buyer_id == user_id) | (Transaction.seller_id == user_id)
        )
        .order_by(Transaction.transaction_date.desc())
        .all()
    )

    return render_template("transactions.html", transactions=transactions)


# Add these routes to your app.py file


@app.route("/toggle_sale_status/<int:land_id>", methods=["POST"])
def toggle_sale_status(land_id):
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    land = Land.query.get_or_404(land_id)

    # Ensure the user owns this land
    if land.owner_id != session["user_id"]:
        flash("You do not have permission to modify this land", "danger")
        return redirect(url_for("landDetails", land_id=land_id))

    try:
        # Toggle for_sale status
        land.for_sale = not land.for_sale
        db.session.commit()

        status = "listed for sale" if land.for_sale else "unlisted from sale"
        flash(f"Land successfully {status}", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"An error occurred: {str(e)}", "danger")

    return redirect(url_for("landDetails", land_id=land_id))


@app.route("/edit_land/<int:land_id>", methods=["GET", "POST"])
def edit_land(land_id):
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    land = Land.query.get_or_404(land_id)

    # Ensure the user owns this land
    if land.owner_id != session["user_id"]:
        flash("You do not have permission to edit this land", "danger")
        return redirect(url_for("landDetails", land_id=land_id))

    if request.method == "POST":
        try:
            land.title = request.form["title"]
            land.location = request.form["location"]
            land.description = request.form["description"]
            land.price = float(request.form["price"])
            land.for_sale = "for_sale" in request.form

            # Update land image if provided
            if "land_image" in request.files:
                file = request.files["land_image"]
                if file.filename:
                    saved_path = save_file(file, "lands")
                    if saved_path:
                        land.image = saved_path

            db.session.commit()

            flash("Land details updated successfully", "success")
            return redirect(url_for("landDetails", land_id=land_id))
        except Exception as e:
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "danger")

    return render_template("edit_land.html", land=land)


@app.route("/api/verify_transaction/<transaction_hash>")
def verify_transaction(transaction_hash):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    transaction = Transaction.query.filter_by(
        blockchain_tx_hash=transaction_hash
    ).first()

    if not transaction:
        return jsonify({"error": "Transaction not found"}), 404

    # In a real application, we would verify this against the blockchain
    # Here we'll simply return the stored information

    result = {
        "verified": True,
        "transaction": {
            "hash": transaction.blockchain_tx_hash,
            "land_id": transaction.land_id,
            "seller": transaction.seller.username,
            "buyer": transaction.buyer.username,
            "price": transaction.price,
            "date": transaction.transaction_date.strftime("%Y-%m-%d %H:%M:%S"),
        },
    }

    return jsonify(result)


@app.route("/search_lands")
def search_lands():
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    query = request.args.get("query", "")

    if query:
        lands = Land.query.filter(
            (
                Land.title.contains(query)
                | Land.location.contains(query)
                | Land.description.contains(query)
            )
            & (Land.for_sale == True)
        ).all()
    else:
        lands = Land.query.filter_by(for_sale=True).all()

    return render_template("search_results.html", lands=lands, query=query)


# API endpoints for blockchain integration
@app.route("/api/lands", methods=["GET"])
def api_get_lands():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    lands = Land.query.all()
    result = []

    for land in lands:
        result.append(
            {
                "id": land.id,
                "blockchain_id": land.blockchain_id,
                "title": land.title,
                "location": land.location,
                "price": land.price,
                "owner_id": land.owner_id,
                "for_sale": land.for_sale,
                "image": url_for(
                    "static", filename=f"uploads/{land.image}", _external=True
                ),
            }
        )

    return jsonify(result)


# Initialize database
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)
