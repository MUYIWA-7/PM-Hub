# =========================
# EMAIL TEMPLATE / SMTP
# =========================

import os
import smtplib

from email.message import EmailMessage
from flask import render_template, url_for
from dotenv import load_dotenv


# Load environment variables
load_dotenv()


# =========================
# SMTP CONFIGURATION
# =========================


MAIL_SERVER = os.getenv("MAIL_SERVER")
MAIL_PORT = int(os.getenv("MAIL_PORT", 587))
MAIL_USERNAME = os.getenv("MAIL_USERNAME")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")


# =========================
# SEND TENANT WELCOME EMAIL
# =========================

def send_tenant_credentials(
    tenant,
    temporary_password
):

    # Create the login URL.
    login_url = url_for(
        "login",
        _external=True
    )

    # Load the HTML email template.
    html_content = render_template(
        "emails/tenant_welcome.html",
        tenant=tenant,
        email=tenant.user.email,
        temporary_password=temporary_password,
        login_url=login_url
    )

    # Create the email.
    message = EmailMessage()

    message["Subject"] = (
        "Welcome to Global Royal Estate Manager"
    )

    message["From"] = MAIL_USERNAME

    message["To"] = tenant.user.email

    # Plain-text fallback.
    message.set_content(
        f"""
Hello {tenant.name},

Your tenant account has been created on
Global Royal Estate Manager.

Login email: {tenant.user.email}
Temporary password: {temporary_password}

Please log in and change your temporary password.

Regards,
Global Royal Estate Manager
"""
    )

    # Add the HTML version.
    message.add_alternative(
        html_content,
        subtype="html"
    )


    # =========================
    # SEND EMAIL
    # =========================

    with smtplib.SMTP(
        MAIL_SERVER,
        MAIL_PORT
    ) as server:

        server.starttls()

        server.login(
            MAIL_USERNAME,
            MAIL_PASSWORD
        )

        server.send_message(message)