# IMPORTS
import os
import smtplib
import secrets
from functools import wraps

from dotenv import load_dotenv

from flask import (
    Flask,
    render_template,
    redirect,
    url_for,
    flash,
    abort
)

from flask_migrate import Migrate

from flask_login import (
    LoginManager,
    login_user,
    logout_user,
    login_required,
    current_user
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from decimal import Decimal
from datetime import date, timedelta

from email_template import send_tenant_credentials

from flask_wtf.csrf import CSRFProtect

from models import (
    db,
    Business,
    User,
    Property,
    Tenant,
    Payment
)

from forms import (
    BusinessSignupForm,
    LoginForm,
    PropertyForm,
    TenantForm,
    PaymentForm
)

load_dotenv()


# =======FLASK APPLICATION==========
app = Flask(__name__)


# =======CONFIGURATION=======
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///GR_estate.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


# ======CSRF PROTECTION======
csrf = CSRFProtect(app)

# ======DATABASE========
db.init_app(app)

# =======LOGIN MANAGER==========
login_manager = LoginManager(app)
login_manager.login_view = "login"
@login_manager.user_loader
def load_user(user_id):

    return db.session.get(
        User,
        int(user_id)
    )

# ======FLASK-MIGRATE========
migrate = Migrate(app, db)


# =========================
# ROLE PROTECTION
# =========================
def manager_required(view):

    @wraps(view)
    @login_required
    def wrapped_view(*args, **kwargs):

        if current_user.role != "manager":

            abort(403)

        return view(*args, **kwargs)

    return wrapped_view


def tenant_required(view):

    @wraps(view)
    @login_required
    def wrapped_view(*args, **kwargs):

        if current_user.role != "tenant":

            abort(403)

        return view(*args, **kwargs)

    return wrapped_view


# =========================
# HOME ROUTE
# =========================
@app.route("/")
def home():

    if current_user.is_authenticated:

        if current_user.role == "tenant":

            return redirect(
                url_for("tenant_dashboard")
            )

        return redirect(
            url_for("manager_dashboard")
        )

    return render_template(
        "home.html"
    )


# =========================
# BUSINESS SIGNUP
# =========================
@app.route("/signup", methods=["GET", "POST"])
def signup():

    form = BusinessSignupForm()

    if form.validate_on_submit():

        # Create the business account.
        business = Business(
            name=form.business_name.data,
            email=form.email.data,
            phone=form.phone.data
        )

        db.session.add(business)

        db.session.flush()

        # Create the manager account.
        user = User(
            name=form.manager_name.data,
            email=form.email.data,
            password=generate_password_hash(
                form.password.data
            ),
            role="manager",
            business_id=business.id
        )

        db.session.add(user)

        db.session.commit()

        return redirect(
            url_for("login")
        )

    return render_template(
        "signup.html",
        form=form
    )


# =========================
# LOGIN
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    form = LoginForm()

    if form.validate_on_submit():

        # Find the user by email.
        user = db.session.scalar(
            db.select(User).where(
                User.email == form.email.data
            )
        )

        # Check that the user exists
        # and the password is correct.
        if user and check_password_hash(
            user.password,
            form.password.data
        ):

            # Log the user into the application.
            login_user(user)

            # Send the user to the correct dashboard based on their role.
            if user.role == "tenant":

                return redirect(
                    url_for("tenant_dashboard")
                )

            return redirect(
                url_for("manager_dashboard")
            )

        else:

            # Invalid email or password.
            flash(
                "Invalid email or password. Please try again.",
                "error"
            )

    return render_template(
        "login.html",
        form=form
    )


# =========================
# LOGOUT
# =========================
@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(
        url_for("home")
    )


# =========================
# NOTIFICATIONS
# =========================
@app.route("/notifications")
@manager_required
def notifications():

    today = date.today()

    ninety_days_from_now = (
        today + timedelta(days=90)
    )

    # Get tenants belonging to the
    # logged-in manager's business.
    tenants = db.session.scalars(
        db.select(Tenant)
        .join(Property)
        .where(
            Property.business_id ==
            current_user.business_id
        )
    ).all()

    expired_tenants = []

    due_soon_tenants = []

    for tenant in tenants:

        # Rent has already expired.
        if tenant.rent_end < today:

            expired_tenants.append(tenant)

        # Rent expires within the next 90 days.
        elif tenant.rent_end <= ninety_days_from_now:

            due_soon_tenants.append(tenant)

    return render_template(
        "notifications.html",
        expired_tenants=expired_tenants,
        due_soon_tenants=due_soon_tenants,
        today=today
    )


# =========================
# NOTIFICATION COUNT
# =========================
@app.context_processor
def notification_count():

    today = date.today()

    ninety_days_from_now = (
        today + timedelta(days=90)
    )

    if (
        current_user.is_authenticated
        and current_user.role == "manager"
    ):

        count = db.session.scalar(
            db.select(
                db.func.count(Tenant.id)
            )
            .join(Property)
            .where(
                Property.business_id ==
                current_user.business_id,

                Tenant.rent_end <=
                ninety_days_from_now
            )
        )

    else:

        count = 0

    return {
        "notification_count": count
    }


# =========================
# MANAGER DASHBOARD
# =========================
@app.route("/dashboard")
@manager_required
def manager_dashboard():

    # Get all properties belonging
    # to the logged-in business.
    properties = db.session.scalars(
        db.select(Property)
        .where(
            Property.business_id ==
            current_user.business_id
        )
    ).all()

    # Total number of properties.
    total_properties = len(properties)

    # Total number of tenants across
    # all properties.
    total_tenants = sum(
        len(property.tenants)
        for property in properties
    )

    # Calculate occupied units using
    # unique unit numbers.
    occupied_units = sum(
        len({
            tenant.unit_number
            for tenant in property.tenants
        })
        for property in properties
    )

    # Calculate vacant units.
    total_units = sum(
        property.total_units
        for property in properties
    )

    vacant_units = (
        total_units - occupied_units
    )

    return render_template(
        "manager_dashboard.html",
        total_properties=total_properties,
        total_tenants=total_tenants,
        occupied_units=occupied_units,
        vacant_units=vacant_units
    )


# =========================
# TENANT DASHBOARD
# =========================
@app.route("/tenant-dashboard")
@tenant_required
def tenant_dashboard():

    # Find the tenant profile belonging
    # to the currently logged-in user.
    tenant = db.session.scalar(
        db.select(Tenant).where(
            Tenant.user_id == current_user.id
        )
    )

    # Make sure the user actually
    # has a tenant profile.
    if tenant is None:

        return "Tenant profile not found", 404

    # Get the tenant's payment records.
    payments = db.session.scalars(
        db.select(Payment)
        .where(
            Payment.tenant_id == tenant.id
        )
        .order_by(
            Payment.payment_date.desc()
        )
    ).all()

    # Calculate total amount paid.
    amount_paid = sum(
        payment.amount
        for payment in payments
    )

    # Calculate outstanding balance.
    outstanding_balance = (
        tenant.annual_rent - amount_paid
    )

    # Determine payment status.
    if amount_paid == 0:

        status = "Unpaid"

    elif amount_paid < tenant.annual_rent:

        status = "Part Paid"

    else:

        status = "Paid"

    return render_template(
        "tenant_dashboard.html",
        tenant=tenant,
        payments=payments,
        amount_paid=amount_paid,
        outstanding_balance=outstanding_balance,
        status=status
    )


# =========================
# ADD PROPERTY
# =========================
@app.route("/add-property", methods=["GET", "POST"])
@manager_required
def add_property():

    form = PropertyForm()

    if form.validate_on_submit():

        new_property = Property(
            name=form.name.data,
            property_type=form.property_type.data,
            total_units=form.total_units.data,
            address=form.address.data,
            business_id=current_user.business_id
        )

        db.session.add(new_property)

        db.session.commit()

        flash(
            "Property added successfully.",
            "success"
        )

        return redirect(
            url_for("properties")
        )

    return render_template(
        "add_property.html",
        form=form
    )


# =========================
# PROPERTIES
# =========================
@app.route("/properties")
@manager_required
def properties():

    properties = db.session.scalars(
        db.select(Property)
        .where(
            Property.business_id ==
            current_user.business_id
        )
    ).all()

    return render_template(
        "properties.html",
        properties=properties
    )


# =========================
# PROPERTY DETAILS
# =========================
@app.route("/properties/<int:property_id>")
@manager_required
def property_details(property_id):

    property = db.session.scalar(
        db.select(Property)
        .where(
            Property.id == property_id,
            Property.business_id ==
            current_user.business_id
        )
    )

    if property is None:

        return "Property not found", 404

    # Calculate payment status
    # for each tenant.
    for tenant in property.tenants:

        amount_paid = sum(
            (
                payment.amount
                for payment in tenant.payments
            ),
            Decimal("0.00")
        )

        if amount_paid == Decimal("0.00"):

            tenant.payment_status = "Unpaid"

        elif amount_paid < tenant.annual_rent:

            tenant.payment_status = "Part Paid"

        else:

            tenant.payment_status = "Paid"

    return render_template(
        "property_details.html",
        property=property
    )


# =========================
# ADD TENANT
# =========================
@app.route("/properties/<int:property_id>/add-tenant", methods=["GET", "POST"])
@manager_required
def add_tenant(property_id):

    # Find the property and make sure
    # it belongs to the logged-in manager's business.
    property = db.session.scalar(
        db.select(Property)
        .where(
            Property.id == property_id,
            Property.business_id ==
            current_user.business_id
        )
    )

    if property is None:

        return "Property not found", 404

    form = TenantForm()

    if form.validate_on_submit():

        # Generate a temporary password
        # for the tenant.
        temporary_password = (
            secrets.token_urlsafe(8)
        )

        # Create the tenant's login account.
        tenant_user = User(
            name=form.name.data,
            email=form.email.data,
            password=generate_password_hash(
                temporary_password
            ),
            role="tenant",
            business_id=current_user.business_id
        )

        db.session.add(tenant_user)

        # Create the tenant profile.
        tenant = Tenant(
            name=form.name.data,
            phone=form.phone.data,
            unit_number=form.unit_number.data,
            move_in_date=form.move_in_date.data,
            annual_rent=form.annual_rent.data,
            rent_start=form.rent_start.data,
            rent_end=form.rent_end.data,
            property_id=property.id,
            user=tenant_user
        )

        db.session.add(tenant)
        db.session.commit()

        # Send the tenant their login credentials by email.
        send_tenant_credentials(
            tenant,
            temporary_password
        )

        flash(
            "Tenant added successfully. Login credentials have been sent to the tenant's email.",
            "success"
        )

        return redirect(
            url_for(
                "property_details",
                property_id=property.id
            )
        )

    return render_template(
        "add_tenant.html",
        form=form,
        property=property
    )


# =========================
# TENANT DETAILS
# =========================
@app.route("/tenants/<int:tenant_id>", methods=["GET", "POST"])
@manager_required
def tenant_details(tenant_id):

    tenant = db.session.scalar(
        db.select(Tenant)
        .join(Property)
        .where(
            Tenant.id == tenant_id,
            Property.business_id ==
            current_user.business_id
        )
    )

    if tenant is None:

        return "Tenant not found", 404

    # Payment form.
    form = PaymentForm()

    # Calculate total amount paid
    # by the tenant.
    amount_paid = sum(
        payment.amount
        for payment in tenant.payments
    )

    # Calculate outstanding balance.
    outstanding_balance = (
        tenant.annual_rent - amount_paid
    )

    # Determine payment status.
    if amount_paid == 0:

        status = "Unpaid"

    elif amount_paid < tenant.annual_rent:

        status = "Part Paid"

    else:

        status = "Paid"

    # Record payment received
    # by the manager.
    if form.validate_on_submit():

        # Prevent overpayment.
        if form.amount.data > outstanding_balance:

            flash(
                "Payment cannot be greater than "
                "the outstanding balance.",
                "error"
            )

            return render_template(
                "tenant_details.html",
                tenant=tenant,
                form=form,
                payments=tenant.payments,
                amount_paid=amount_paid,
                outstanding_balance=
                    outstanding_balance,
                status=status,
                formatted_annual_rent=
                    f"{tenant.annual_rent:,.2f}",
                formatted_amount_paid=
                    f"{amount_paid:,.2f}",
                formatted_outstanding_balance=
                    f"{outstanding_balance:,.2f}"
            )

        new_payment = Payment(
            amount=form.amount.data,
            payment_date=form.payment_date.data,
            tenant_id=tenant.id
        )

        db.session.add(new_payment)

        db.session.commit()

        flash(
            "Payment recorded successfully.",
            "success"
        )

        return redirect(
            url_for(
                "tenant_details",
                tenant_id=tenant.id
            )
        )

    return render_template(
        "tenant_details.html",
        tenant=tenant,
        form=form,
        payments=tenant.payments,
        amount_paid=amount_paid,
        outstanding_balance=outstanding_balance,
        status=status,
        formatted_annual_rent=
            f"{tenant.annual_rent:,.2f}",
        formatted_amount_paid=
            f"{amount_paid:,.2f}",
        formatted_outstanding_balance=
            f"{outstanding_balance:,.2f}"
    )


# =========================
# EDIT TENANT
# =========================
@app.route("/tenants/<int:tenant_id>/edit", methods=["GET", "POST"])
@manager_required
def edit_tenant(tenant_id):

    tenant = db.session.scalar(
        db.select(Tenant)
        .join(Property)
        .where(
            Tenant.id == tenant_id,
            Property.business_id ==
            current_user.business_id
        )
    )

    if tenant is None:

        return "Tenant not found", 404

    form = TenantForm(obj=tenant)

    if form.validate_on_submit():

        tenant.name = form.name.data

        tenant.phone = form.phone.data

        tenant.unit_number = form.unit_number.data

        tenant.move_in_date = (
            form.move_in_date.data
        )

        tenant.annual_rent = (
            form.annual_rent.data
        )

        tenant.rent_start = (
            form.rent_start.data
        )

        tenant.rent_end = (
            form.rent_end.data
        )

        db.session.commit()

        flash(
            "Tenant updated successfully.",
            "success"
        )

        return redirect(
            url_for(
                "property_details",
                property_id=tenant.property_id
            )
        )

    return render_template(
        "edit_tenant.html",
        form=form,
        tenant=tenant
    )


# =========================
# DELETE TENANT
# =========================
@app.route("/tenants/<int:tenant_id>/delete", methods=["POST"])
@manager_required
def delete_tenant(tenant_id):

    # Find the tenant and make sure the tenant
    # belongs to the logged-in manager's business.
    tenant = db.session.scalar(
        db.select(Tenant)
        .join(Property)
        .where(
            Tenant.id == tenant_id,
            Property.business_id == current_user.business_id
        )
    )

    if tenant is None:
        return "Tenant not found", 404

    # Save the property ID before deleting the tenant.
    property_id = tenant.property_id

    # Get the tenant's login account.
    tenant_user = tenant.user

    # Delete all payment records belonging to the tenant.
    for payment in tenant.payments:
        db.session.delete(payment)

    # Delete the tenant profile.
    db.session.delete(tenant)

    # Delete the tenant's login account.
    if tenant_user:
        db.session.delete(tenant_user)

    db.session.commit()

    flash(
        "Tenant deleted successfully.",
        "success"
    )

    return redirect(
        url_for(
            "property_details",
            property_id=property_id
        )
    )


# =========================
# RUN APPLICATION
# =========================

if __name__ == "__main__":

    app.run(debug=True)