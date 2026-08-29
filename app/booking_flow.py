import re
from datetime import datetime, date


REQUIRED_FIELDS = [
    "name",
    "email",
    "phone",
    "booking_type",
    "date",
    "time",
]


def create_empty_booking():
    """Create a new empty booking object."""

    return {
        "name": None,
        "email": None,
        "phone": None,
        "booking_type": None,
        "date": None,
        "time": None,
    }


def get_missing_fields(booking):
    """Return fields that still need to be collected."""

    return [
        field
        for field in REQUIRED_FIELDS
        if not booking.get(field)
    ]


def get_next_question(booking):
    """Ask only for the next missing booking detail."""

    missing_fields = get_missing_fields(booking)

    if not missing_fields:
        return None

    next_field = missing_fields[0]

    questions = {
        "name": "What is your full name?",
        "email": "What is your email address?",
        "phone": "What is your phone number?",
        "booking_type": "What would you like to book?",
        "date": (
            "What date would you prefer? "
            "Please use YYYY-MM-DD."
        ),
        "time": (
            "What time would you prefer? "
            "Please use HH:MM (24-hour format), "
            "for example 14:30."
        ),
    }

    return questions[next_field]


# -------------------------------------------------
# VALIDATION FUNCTIONS
# -------------------------------------------------


def validate_name(name):
    """Validate a customer's name."""

    name = name.strip()

    if len(name) < 2:
        return False

    if not any(char.isalpha() for char in name):
        return False

    return True


def validate_email(email):
    """Basic email validation."""

    pattern = (
        r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    )

    return (
        re.match(
            pattern,
            email,
        )
        is not None
    )


def validate_phone(phone):
    """Validate phone number."""

    digits = re.sub(
        r"\D",
        "",
        phone,
    )

    return 10 <= len(digits) <= 15


def validate_booking_type(booking_type):
    """Validate booking/service type."""

    return len(
        booking_type.strip()
    ) >= 2


def validate_date(date_string):
    """
    Validate YYYY-MM-DD format
    and reject past dates.
    """

    try:

        booking_date = (
            datetime.strptime(
                date_string,
                "%Y-%m-%d",
            ).date()
        )

        if booking_date < date.today():
            return False

        return True

    except ValueError:

        return False


def validate_time(time_string):
    """
    Validate HH:MM 24-hour format.
    """

    try:

        datetime.strptime(
            time_string,
            "%H:%M",
        )

        return True

    except ValueError:

        return False


# -------------------------------------------------
# UPDATE BOOKING FIELD
# -------------------------------------------------


def update_booking_field(
    booking,
    field,
    value,
):
    """
    Validate and update one booking field.

    Returns:
        success: bool
        message: str
    """

    value = value.strip()


    # ---------------------------------------------
    # EMPTY VALUE
    # ---------------------------------------------

    if not value:

        return (
            False,
            "This field cannot be empty. "
            "Please try again.",
        )


    # ---------------------------------------------
    # NAME
    # ---------------------------------------------

    if field == "name":

        if not validate_name(value):

            return (
                False,
                "Please enter a valid full name.",
            )


    # ---------------------------------------------
    # EMAIL
    # ---------------------------------------------

    elif field == "email":

        if not validate_email(value):

            return (
                False,
                "That doesn't look like a valid "
                "email address. Please try again.",
            )


    # ---------------------------------------------
    # PHONE
    # ---------------------------------------------

    elif field == "phone":

        if not validate_phone(value):

            return (
                False,
                "Please enter a valid phone number "
                "containing 10 to 15 digits.",
            )


    # ---------------------------------------------
    # BOOKING TYPE
    # ---------------------------------------------

    elif field == "booking_type":

        if not validate_booking_type(value):

            return (
                False,
                "Please enter a valid booking "
                "or service type.",
            )


    # ---------------------------------------------
    # DATE
    # ---------------------------------------------

    elif field == "date":

        try:

            booking_date = (
                datetime.strptime(
                    value,
                    "%Y-%m-%d",
                ).date()
            )

        except ValueError:

            return (
                False,
                "Please enter the date as "
                "**YYYY-MM-DD**.",
            )

        if booking_date < date.today():

            return (
                False,
                "Please choose today or a future "
                "date. Past dates cannot be booked.",
            )


    # ---------------------------------------------
    # TIME
    # ---------------------------------------------

    elif field == "time":

        if not validate_time(value):

            return (
                False,
                "Please enter the time as "
                "**HH:MM** in 24-hour format. "
                "For example: **14:30**.",
            )


    # ---------------------------------------------
    # SAVE VALID VALUE
    # ---------------------------------------------

    booking[field] = value


    return (
        True,
        "Updated successfully.",
    )


# -------------------------------------------------
# BOOKING SUMMARY
# -------------------------------------------------


def format_booking_summary(booking):
    """Create a confirmation summary."""

    return f"""
Please confirm your booking:

**Name:** {booking['name']}
**Email:** {booking['email']}
**Phone:** {booking['phone']}
**Booking Type:** {booking['booking_type']}
**Date:** {booking['date']}
**Time:** {booking['time']}

Reply **YES** to confirm or **NO** to cancel.
"""