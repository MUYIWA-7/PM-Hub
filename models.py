from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# We will connect this object to the Flask application inside app.py using: db.init_app(app)
db = SQLAlchemy()


# =========================
# BUSINESS MODEL
# =========================
class Business(db.Model):
    
    __tablename__ = "businesses"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)

    email = db.Column(db.String(150), nullable=False, unique=True)

    phone = db.Column(db.String(30), nullable=True)

    def __repr__(self):

        return f"<Business {self.name}>"


# =========================
# USER MODEL
# =========================
class User(UserMixin, db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)

    email = db.Column(db.String(150), nullable=False, unique=True)

    password = db.Column(db.String(255), nullable=False)

    # Defines what type of user this is.
    # Examples: "manager" or "tenant"
    role = db.Column(db.String(20), nullable=False, default="manager")

    # Connect the user to their business.
    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False)

    # Allows us to access the user's business using:
    # user.business
    business = db.relationship("Business", backref="users")


# =========================
# PROPERTY MODEL
# =========================
class Property(db.Model):

    __tablename__ = "properties"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)

    property_type = db.Column(db.String(50), nullable=False)

    # Total number of units in the property.
    total_units = db.Column(db.Integer, nullable=False)

    address = db.Column(db.String(255), nullable=True)

    business_id = db.Column(db.Integer, db.ForeignKey("businesses.id"), nullable=False)

    business = db.relationship("Business", backref="properties")


# =========================
# TENANT MODEL
# =========================
class Tenant(db.Model):

    __tablename__ = "tenants"

    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(150), nullable=False)

    phone = db.Column(db.String(30), nullable=False)

    unit_number = db.Column(db.String(50), nullable=False)

    move_in_date = db.Column(db.Date, nullable=False)

    annual_rent = db.Column(db.Numeric(10, 2), nullable=False)

    rent_start = db.Column(db.Date, nullable=False)

    rent_end = db.Column(db.Date, nullable=False)

    property_id = db.Column(db.Integer, db.ForeignKey("properties.id"), nullable=False)

    # Link the tenant to their login account.
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True, unique=True)

    # Connect the tenant to their property.
    property = db.relationship("Property", backref="tenants")

    # Connect the tenant to their user account.
    user = db.relationship("User", backref="tenant_profile", uselist=False)


# =========================
# PAYMENT MODEL
# =========================
class Payment(db.Model):

    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)

    amount = db.Column(db.Numeric(10, 2), nullable=False)

    payment_date = db.Column(db.Date, nullable=False)

    tenant_id = db.Column(db.Integer, db.ForeignKey("tenants.id"), nullable=False)

    # Connect each payment to its tenant.
    tenant = db.relationship("Tenant", backref="payments")










