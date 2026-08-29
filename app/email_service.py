import smtplib
import streamlit as st

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_booking_confirmation(booking, booking_id):
    """
    Send a booking confirmation email.

    Returns:
        (True, message) if email was sent successfully.
        (False, message) if email sending failed.
    """

    sender_email = st.secrets["SENDER_EMAIL"]
    sender_password = st.secrets["SENDER_APP_PASSWORD"]

    receiver_email = booking["email"]

    subject = f"Booking Confirmed - Booking #{booking_id}"

    body = f"""
Hello {booking["name"]},

Your booking has been successfully confirmed.

Booking Details
----------------------------

Booking ID: {booking_id}
Booking Type: {booking["booking_type"]}
Date: {booking["date"]}
Time: {booking["time"]}

We look forward to assisting you.

Regards,
AI Booking Assistant
"""

    message = MIMEMultipart()

    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(
        MIMEText(body, "plain")
    )

    try:

        with smtplib.SMTP(
            "smtp.gmail.com",
            587,
        ) as server:

            server.starttls()

            server.login(
                sender_email,
                sender_password,
            )

            server.send_message(
                message
            )

        return (
            True,
            "Confirmation email sent successfully.",
        )

    except Exception as error:

        return (
            False,
            str(error),
        )