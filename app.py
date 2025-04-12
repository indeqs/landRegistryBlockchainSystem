from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    send_file,
    session,
    jsonify,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os, io
import qrcode
from web3 import Web3
import json
from os import getenv
from datetime import datetime, timezone
import uuid

"""
Land Registry Blockchain Application
-----------------------------------
A Flask web application for managing land registry records 
using blockchain technology for secure, transparent land ownership records.

Features:
- User registration and authentication
- Land registration with blockchain verification
- Land marketplace with buying and selling capabilities
- QR code generation for land verification
- Transaction history tracking
"""

# App configuration
app = Flask(__name__)
app.config["SECRET_KEY"] = getenv("SECRET")
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

# Ethereum Configuration
ALCHEMY_URL = getenv("RPC_URL")  # Get RPC URL from environment variables
w3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

# Load smart contract ABI and address
with open("src/contract_abi.json", "r") as f:
    contract_abi = json.load(f)

contract_address = "0x322D4Ab5baC728982Fb228CC37f527b599817836"
land_registry_contract = w3.eth.contract(address=contract_address, abi=contract_abi)


# Database models
class User(db.Model):
    """
    User model representing registered users in the system.

    Attributes:
        id: Unique identifier for the user
        username: User's chosen username
        email: User's email address
        password_hash: Hashed password for security
        blockchain_address: User's Ethereum wallet address
        profile_image: Path to user's profile image
        created_at: Timestamp when the user account was created
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    blockchain_address = db.Column(db.String(42), unique=True, nullable=False)
    profile_image = db.Column(db.String(200), default="default_profile.jpg")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<User {self.username}>"


class Land(db.Model):
    """
    Land model representing land parcels registered in the system.

    Attributes:
        id: Unique identifier for the land record
        blockchain_id: Corresponding ID in the blockchain
        owner_id: ID of the user who owns the land
        title: Title of the land
        location: Physical location of the land
        description: Detailed description of the land
        price: Asking price for the land (if for sale)
        image: Path to land's image
        for_sale: Whether the land is currently listed for sale
        created_at: Timestamp when the land was registered
    """

    id = db.Column(db.Integer, primary_key=True)
    blockchain_id = db.Column(db.Integer, unique=True, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    image = db.Column(db.String(200))
    for_sale = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    owner = db.relationship("User", backref=db.backref("lands", lazy=True))

    def __repr__(self):
        return f"<Land {self.title}>"


class Transaction(db.Model):
    """
    Transaction model recording land ownership transfers.

    Attributes:
        id: Unique identifier for the transaction
        blockchain_tx_hash: Hash of the blockchain transaction
        land_id: ID of the land being transferred
        seller_id: ID of the user selling the land
        buyer_id: ID of the user buying the land
        price: Price at which the land was sold
        transaction_date: Timestamp when the transaction occurred
    """

    id = db.Column(db.Integer, primary_key=True)
    blockchain_tx_hash = db.Column(db.String(66), unique=True, nullable=False)
    land_id = db.Column(db.Integer, db.ForeignKey("land.id"), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    buyer_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    price = db.Column(db.Float, nullable=False)
    transaction_date = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc)
    )

    land = db.relationship("Land", backref=db.backref("transactions", lazy=True))
    seller = db.relationship("User", foreign_keys=[seller_id])
    buyer = db.relationship("User", foreign_keys=[buyer_id])

    def __repr__(self):
        return f"<Transaction {self.blockchain_tx_hash[:10]}>"


# Helper functions
def allowed_file(filename):
    """
    Check if a file has an allowed extension for upload.

    Args:
        filename: Name of the file to check

    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_file(file, folder):
    """
    Save an uploaded file with a unique name in the specified folder.

    Args:
        file: The file object to save
        folder: The subfolder within UPLOAD_FOLDER to save to

    Returns:
        str: Path to the saved file relative to the uploads directory, or None if save failed
    """
    if file and allowed_file(file.filename):
        # Generate unique filename using UUID to prevent overwriting
        filename = str(uuid.uuid4()) + "." + file.filename.rsplit(".", 1)[1].lower()
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], folder, filename)
        file.save(file_path)
        # Return the path relative to the uploads directory for consistency
        if folder == "profiles":
            return filename  # Just return filename for profile images to maintain consistency
        else:
            return os.path.join(folder, filename)
    return None


# Routes
@app.route("/")
def index():
    """Homepage route"""
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    User registration route.

    GET: Display registration form
    POST: Process registration data
    """
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
        wallet = (
            w3.eth.account.create()
        )  # Create a new Ethereum account. Don't use this. There should a connect wallet button wallet

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
    """
    User login route.

    GET: Display login form
    POST: Process login credentials
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            # Store user data in session
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
    """Log user out by clearing session data"""
    session.clear()
    flash("You have been logged out", "info")
    return redirect(url_for("index"))


@app.route("/dashboard")
def dashboard():
    """
    User dashboard showing owned lands.

    Requires authentication.
    """
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    user = User.query.filter_by(id=session["user_id"]).first()
    if not user:
        flash("User not found", "danger")
        return redirect(url_for("logout"))

    # Get lands owned by the user
    user_lands = Land.query.filter_by(owner_id=user.id).all()

    return render_template("dashboard.html", user=user, lands=user_lands)


@app.route("/profile", methods=["GET", "POST"])
def profile():
    """
    User profile management route.

    GET: Display user profile
    POST: Update profile data (currently just profile image)

    Requires authentication.
    """
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
                    # Store just the filename for profile images
                    user.profile_image = saved_path
                    db.session.commit()
                    flash("Profile image updated successfully", "success")

        return redirect(url_for("profile"))

    return render_template("profile.html", user=user)

@app.route('/update_wallet_address', methods=['POST'])
def update_wallet_address():
    """
    Update user's blockchain wallet address.
    
    Used when a user connects their MetaMask wallet.
    
    Requires authentication.
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        address = data.get('address')
        
        if not address or not address.startswith('0x') or len(address) != 42:
            return jsonify({'success': False, 'error': 'Invalid wallet address'}), 400
        
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user.blockchain_address = address
        db.session.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500
    

@app.route("/registerLand", methods=["GET", "POST"])
def registerLand():
    """
    Land registration route.

    GET: Display land registration form
    POST: Process land registration data for blockchain transaction

    Requires authentication.
    """
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        location = request.form["location"]
        description = request.form["description"]
        price = float(request.form["price"])
        for_sale = "for_sale" in request.form
        blockchain_tx_hash = request.form.get("blockchain_tx_hash")
        blockchain_id = request.form.get("blockchain_id")
        
        # Save land image
        land_image = "default_land.png"
        if "land_image" in request.files:
            file = request.files["land_image"]
            if file.filename:
                saved_path = save_file(file, "lands")
                if saved_path:
                    land_image = saved_path

        # If we have a blockchain transaction hash and ID, save the land to database
        if blockchain_tx_hash and blockchain_id:
            try:
                # Create local record
                new_land = Land(
                    blockchain_id=int(blockchain_id),
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

                flash("Land registered successfully on the blockchain!", "success")
                return redirect(url_for("dashboard"))
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred: {str(e)}", "danger")
                return redirect(url_for("registerLand"))
        else:
            # This is the initial form submission without blockchain confirmation
            # Just render the template with the form data for the frontend to handle the transaction
            return render_template(
                "registerLand.html", 
                form_data={
                    'title': title,
                    'location': location,
                    'description': description,
                    'price': price,
                    'for_sale': for_sale,
                    'image': land_image if land_image != "default_land.png" else None
                }
            )

    return render_template("registerLand.html")


@app.route("/marketplace")
def marketplace():
    """
    Land marketplace route displaying all lands for sale.

    Requires authentication.
    """
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    lands_for_sale = Land.query.filter_by(for_sale=True).all()
    return render_template("marketplace.html", lands=lands_for_sale)


@app.route("/land/<int:land_id>")
def landDetails(land_id):
    """
    Display detailed information about a specific land.

    Args:
        land_id: ID of the land to display

    Requires authentication.
    """
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    land = Land.query.get_or_404(land_id)
    return render_template("landDetails.html", land=land)


@app.route("/landQR/<int:land_id>")
def landQR(land_id):
    """
    Generate QR code for land verification.

    Args:
        land_id: ID of the land to generate QR code for

    Returns:
        PNG image of QR code

    Requires authentication.
    """
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    land = Land.query.get_or_404(land_id)

    # Create a QR code that links to your verification URL
    verification_url = url_for("landDetails", land_id=land.id, _external=True)

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(verification_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")

    # Save image to memory buffer
    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)

    return send_file(img_bytes, mimetype="image/png")


@app.route("/buyLand/<int:land_id>", methods=["POST"])
def buyLand(land_id):
    """
    Process land purchase transaction.

    Args:
        land_id: ID of the land to purchase

    Requires authentication.
    """
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    land = Land.query.get_or_404(land_id)
    buyer_id = session["user_id"]

    # Validate purchase conditions
    if land.owner_id == buyer_id:
        flash("You already own this land", "warning")
        return redirect(url_for("landDetails", land_id=land_id))

    if not land.for_sale:
        flash("This land is not for sale", "warning")
        return redirect(url_for("landDetails", land_id=land_id))

    # Get blockchain transaction hash from form
    blockchain_tx_hash = request.form.get("blockchain_tx_hash")
    
    if blockchain_tx_hash:
        try:
            # Record the transaction
            transaction = Transaction(
                blockchain_tx_hash=blockchain_tx_hash,
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
    else:
        # No blockchain transaction hash - return to land details
        flash("Blockchain transaction required to complete purchase", "warning")
        return redirect(url_for("landDetails", land_id=land_id))


@app.route("/transactions")
def transaction_history():
    """
    Display user's transaction history.

    Shows transactions where the user is either buyer or seller.

    Requires authentication.
    """
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


@app.route("/toggle_sale_status/<int:land_id>", methods=["POST"])
def toggle_sale_status(land_id):
    """
    Toggle the for_sale status of a land.

    Args:
        land_id: ID of the land to update

    Requires authentication and ownership of the land.
    """
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


@app.route("/editLand/<int:land_id>", methods=["GET", "POST"])
def editLand(land_id):
    """
    Edit land details.

    GET: Display land edit form
    POST: Process land updates with blockchain transaction

    Args:
        land_id: ID of the land to edit

    Requires authentication and ownership of the land.
    """
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    land = Land.query.get_or_404(land_id)

    # Ensure the user owns this land
    if land.owner_id != session["user_id"]:
        flash("You do not have permission to edit this land", "danger")
        return redirect(url_for("landDetails", land_id=land_id))

    if request.method == "POST":
        blockchain_tx_hash = request.form.get("blockchain_tx_hash")
        
        # Only update if we have blockchain confirmation
        if blockchain_tx_hash:
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

                flash("Land details updated successfully on the blockchain", "success")
                return redirect(url_for("landDetails", land_id=land_id))
            except Exception as e:
                db.session.rollback()
                flash(f"An error occurred: {str(e)}", "danger")
        else:
            # Form submission without blockchain transaction - return the form with values
            return render_template(
                "editLand.html", 
                land=land,
                form_submission=True
            )

    return render_template("editLand.html", land=land)


@app.route("/api/verify_transaction/<transaction_hash>")
def verify_transaction(transaction_hash):
    """
    API endpoint to verify transaction authenticity.

    Args:
        transaction_hash: Hash of the blockchain transaction to verify

    Returns:
        JSON response with transaction details

    Requires authentication.
    """
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


@app.route("/seacrhLands")
def seacrhLands():
    """
    Search lands by title, location, or description.

    Query Parameters:
        query: Search terms

    Requires authentication.
    """
    if "user_id" not in session:
        flash("Please log in first", "warning")
        return redirect(url_for("login"))

    query = request.args.get("query", "")

    if query:
        # Search for lands matching the query that are for sale
        lands = Land.query.filter(
            (
                Land.title.contains(query)
                | Land.location.contains(query)
                | Land.description.contains(query)
            )
            & (Land.for_sale == True)
        ).all()
    else:
        # If no query, show all lands for sale
        lands = Land.query.filter_by(for_sale=True).all()

    return render_template("searchResults.html", lands=lands, query=query)


@app.route("/api/lands", methods=["GET"])
def api_get_lands():
    """
    API endpoint to get all lands.

    Returns:
        JSON list of all lands

    Requires authentication.
    """
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
