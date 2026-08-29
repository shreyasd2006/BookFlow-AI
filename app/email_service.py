import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import streamlit as st


def send_email(to_email, subject, body):
    """
    Generic SMTP email tool.
    Returns (success, message).
    """
    try:
        sender_email = st.secrets["SENDER_EMAIL"]
        sender_password = st.secrets["SENDER_APP_PASSWORD"]

        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = to_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(message)

        return True, "Confirmation email sent successfully."

    except Exception as error:
        return False, str(error)


def send_booking_confirmation(booking, booking_id):
    """Send a restaurant reservation confirmation."""
    extras = []

    if booking.get("occasion"):
        extras.append(f"Occasion: {booking['occasion']}")
    if booking.get("dietary_requirements"):
        extras.append(
            f"Dietary requirements: {booking['dietary_requirements']}"
        )
    if booking.get("special_requests"):
        extras.append(
            f"Special requests: {booking['special_requests']}"
        )

    extra_text = "\n".join(extras)
    if extra_text:
        extra_text = "\n" + extra_text

    subject = f"Restaurant Reservation Confirmed - #{booking_id}"

    body = f"""
Hello {booking['name']},

Your restaurant reservation has been confirmed.

Reservation details
-------------------
Reservation ID: {booking_id}
Guests: {booking['number_of_guests']}
Date: {booking['date']}
Time: {booking['time']}
Email: {booking['email']}
Phone: {booking['phone']}
{extra_text}

Thank you for choosing our restaurant.

Regards,
The Garden Table
AI Reservation Assistant
"""

    return send_email(
        to_email=booking["email"],
        subject=subject,
        body=body,
    )
