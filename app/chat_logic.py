from app.tools import analyze_booking_message, generate_ai_response


BOOKING_KEYWORDS = {
    "book",
    "booking",
    "reserve",
    "reservation",
    "table",
    "restaurant",
    "dinner",
    "lunch",
}


def analyze_message(message, booking, booking_active=False):
    """Use Gemini for intent/detail extraction with a small safety fallback."""
    try:
        return analyze_booking_message(
            message=message,
            booking=booking,
            booking_active=booking_active,
        )
    except Exception:
        lowered = str(message).lower()
        likely_booking = any(word in lowered for word in BOOKING_KEYWORDS)
        return {
            "intent": "booking" if likely_booking or booking_active else "general",
            "name": None,
            "email": None,
            "phone": None,
            "number_of_guests": None,
            "date": None,
            "time": None,
            "occasion": None,
            "dietary_requirements": None,
            "special_requests": None,
        }


def generate_general_response(message, chat_history, vector_store=None):
    return generate_ai_response(
        user_message=message,
        chat_history=chat_history,
        vector_store=vector_store,
    )
