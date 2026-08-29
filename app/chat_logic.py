from app.tools import generate_ai_response


BOOKING_KEYWORDS = [
    "book",
    "booking",
    "appointment",
    "reserve",
    "reservation",
    "schedule",
]


def detect_intent(message):
    """
    Detect whether the user is trying to make a booking.
    """

    message_lower = message.lower()

    for keyword in BOOKING_KEYWORDS:

        if keyword in message_lower:
            return "booking"

    return "general"


def generate_general_response(
    message,
    chat_history,
    vector_store=None,
):
    """
    Generate an AI response using Gemini.

    The response can use:
    - Recent conversation history
    - Retrieved PDF context
    """

    return generate_ai_response(
        user_message=message,
        chat_history=chat_history,
        vector_store=vector_store,
    )