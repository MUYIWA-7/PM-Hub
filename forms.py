from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField, IntegerField, DecimalField, DateField
from wtforms.validators import DataRequired, Email, Length, EqualTo, NumberRange


# =========================
# BUSINESS SIGNUP FORM
# =========================
class BusinessSignupForm(FlaskForm):

    business_name = StringField(
        "Business Name",
        validators=[DataRequired(), Length(min=2, max=150)]
    )

    manager_name = StringField(
        "Manager Name",
        validators=[DataRequired(), Length(min=2, max=150)]
    )

    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )

    phone = StringField(
        "Phone Number",
        validators=[DataRequired(), Length(min=7, max=30)]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=8, max=255)]
    )

    confirm_password = PasswordField(
        "Confirm Password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")]
    )

    submit = SubmitField("Create Account")


# =========================
# LOGIN FORM
# =========================
class LoginForm(FlaskForm):

    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )

    password = PasswordField(
        "Password",
        validators=[DataRequired()]
    )

    submit = SubmitField("Login")


# =========================
# PROPERTY FORM
# =========================
class PropertyForm(FlaskForm):

    name = StringField(
        "Property Name",
        validators=[DataRequired(), Length(min=2, max=150)]
    )

    property_type = SelectField(
        "Property Type",
        choices=[
            ("Apartment", "Apartment"),
            ("Hostel", "Hostel"),
            ("House", "House"),
            ("Office", "Office"),
            ("Shop", "Shop"),
            ("Other", "Other")
        ],
        validators=[DataRequired()]
    )

    total_units = IntegerField(
        "Total Units",
        validators=[
            DataRequired(),
            NumberRange(min=1)
        ]
    )

    address = StringField(
        "Property Address",
        validators=[Length(max=255)]
    )

    submit = SubmitField("Add Property")


# =========================
# TENANT FORM
# =========================
class TenantForm(FlaskForm):

    name = StringField(
        "Tenant Name",
        validators=[DataRequired(), Length(min=2, max=150)]
    )

    phone = StringField(
        "Phone Number",
        validators=[DataRequired(), Length(max=30)]
    )

    email = StringField(
        "Email",
        validators=[DataRequired(), Email()]
    )

    unit_number = StringField(
        "Unit Number",
        validators=[DataRequired(), Length(max=50)]
    )

    move_in_date = DateField(
        "Move-in Date",
        validators=[DataRequired()],
        format="%Y-%m-%d"
    )

    annual_rent = DecimalField(
        "Annual Rent",
        validators=[DataRequired(), NumberRange(min=0)],
        places=2
    )

    rent_start = DateField(
        "Rent Start Date",
        validators=[DataRequired()]
    )

    rent_end = DateField(
        "Rent End Date",
        validators=[DataRequired()]
    )

    submit = SubmitField("Add Tenant")


# =========================
# PAYMENT FORM
# =========================
class PaymentForm(FlaskForm):

    amount = DecimalField(
        "Amount Paid",
        validators=[
            DataRequired(),
            NumberRange(min=0)
        ],
        places=2
    )

    payment_date = DateField(
        "Payment Date",
        validators=[
            DataRequired()
        ],
        format="%Y-%m-%d"
    )

    submit = SubmitField("Record Payment")


