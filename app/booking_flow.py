import re
from datetime import date, datetime


REQUIRED_FIELDS = [
    "name",
    "email",
    "phone",
    "number_of_guests",
    "date",
    "time",
]


QUESTIONS = {
    "name": "May I have the name for the reservation?",
    "email": "What email address should I use for the reservation confirmation?",
    "phone": "What phone number should I attach to the reservation?",
    "number_of_guests": "How many guests will be joining you?",
    "date": "What date would you like? Please use YYYY-MM-DD, or say something like 'tomorrow'.",
    "time": "What time would you like? You can say '8 PM' or use HH:MM.",
}


def create_empty_booking():
    return {
        "name": None,
        "email": None,
        "phone": None,
        "booking_type": "Restaurant Table Reservation",
        "number_of_guests": None,
        "date": None,
        "time": None,
        "occasion": None,
        "dietary_requirements": None,
        "special_requests": None,
    }


def get_missing_fields(booking):
    return [field for field in REQUIRED_FIELDS if not booking.get(field)]


def get_next_question(booking):
    missing = get_missing_fields(booking)
    return QUESTIONS[missing[0]] if missing else None


def validate_name(name):
    value = str(name).strip()
    return len(value) >= 2 and any(char.isalpha() for char in value)


def validate_email(email):
    return re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", str(email).strip()) is not None


def validate_phone(phone):
    digits = re.sub(r"\D", "", str(phone))
    return 10 <= len(digits) <= 15


def validate_number_of_guests(value):
    try:
        guests = int(value)
        return 1 <= guests <= 50
    except (TypeError, ValueError):
        return False


def validate_date(date_string):
    try:
        booking_date = datetime.strptime(str(date_string).strip(), "%Y-%m-%d").date()
        return booking_date >= date.today()
    except ValueError:
        return False


def validate_time(time_string):
    try:
        datetime.strptime(str(time_string).strip(), "%H:%M")
        return True
    except ValueError:
        return False


def update_booking_field(booking, field, value):
    value = str(value).strip()

    if not value:
        return False, "This field cannot be empty. Please try again."

    if field == "name" and not validate_name(value):
        return False, "Please enter a valid name."

    if field == "email" and not validate_email(value):
        return False, "That doesn't look like a valid email address. Please try again."

    if field == "phone" and not validate_phone(value):
        return False, "Please enter a valid phone number containing 10–15 digits."

    if field == "number_of_guests":
        if not validate_number_of_guests(value):
            return False, "Please enter a guest count between 1 and 50."
        booking[field] = int(value)
        return True, "Updated successfully."

    if field == "date" and not validate_date(value):
        return False, "Please enter a valid future date as YYYY-MM-DD."

    if field == "time":
        if not validate_time(value):
            return False, "Please enter the time as HH:MM, for example 20:00."

    booking[field] = value
    return True, "Updated successfully."


def merge_extracted_details(booking, extracted):
    """Merge Gemini-extracted booking fields into the current state."""
    field_names = [
        "name",
        "email",
        "phone",
        "number_of_guests",
        "date",
        "time",
        "occasion",
        "dietary_requirements",
        "special_requests",
    ]

    for field in field_names:
        value = extracted.get(field)
        if value is None or str(value).strip() == "":
            continue

        if field == "number_of_guests":
            try:
                value = int(value)
            except (TypeError, ValueError):
                continue

        booking[field] = value


def format_booking_summary(booking):
    optional_lines = []

    if booking.get("occasion"):
        optional_lines.append(f"**Occasion:** {booking['occasion']}")

    if booking.get("dietary_requirements"):
        optional_lines.append(
            f"**Dietary requirements:** {booking['dietary_requirements']}"
        )

    if booking.get("special_requests"):
        optional_lines.append(
            f"**Special requests:** {booking['special_requests']}"
        )

    extras = "\n".join(optional_lines)
    if extras:
        extras = "\n" + extras

    return (
        "### 🍽️ Reservation Summary\n\n"
        f"**Name:** {booking['name']}\n\n"
        f"**Guests:** {booking['number_of_guests']}\n\n"
        f"**Date:** {booking['date']}\n\n"
        f"**Time:** {booking['time']}\n\n"
        f"**Email:** {booking['email']}\n\n"
        f"**Phone:** {booking['phone']}\n"
        f"{extras}\n\n"
        "Please reply **YES** to confirm or **NO** to cancel."
    )
