import json
from datetime import date

import streamlit as st
from google import genai

from app.config import (
    AI_MEMORY_LIMIT,
    GEMINI_MODEL,
    TOP_K_RETRIEVAL,
    RESTAURANT_NAME,
    RESTAURANT_DESCRIPTION,
)
from app.rag_pipeline import retrieve_relevant_chunks


def get_gemini_client():
    api_key = st.secrets["GEMINI_API_KEY"]
    return genai.Client(api_key=api_key)


def safe_json_from_text(text):
    """Parse JSON even if the model wraps it in markdown fences."""
    cleaned = str(text).strip()

    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        cleaned = cleaned.rsplit("```", 1)[0].strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def analyze_booking_message(message, booking, booking_active=False):
    """
    Use Gemini to understand restaurant-reservation intent and extract
    any details already present in a user's message.
    """
    client = get_gemini_client()

    today = date.today().isoformat()
    current_state = json.dumps(booking, ensure_ascii=False)

    prompt = f"""
Today is {today}.

You are the reservation-intelligence component for {RESTAURANT_NAME}.
{RESTAURANT_DESCRIPTION}

Analyze the user's latest message.

Return ONLY valid JSON with exactly these keys:

intent: one of "booking", "general", "unclear"
name: string or null
email: string or null
phone: string or null
number_of_guests: integer or null
date: YYYY-MM-DD string or null
time: HH:MM 24-hour string or null
occasion: string or null
dietary_requirements: string or null
special_requests: string or null

Rules:
- Interpret natural language such as "tomorrow", "this Friday", "8 PM", "for five", etc.
- Convert relative dates into YYYY-MM-DD using today's date.
- Convert 12-hour times into HH:MM.
- A message like "book a table", "reserve dinner", "get me a table", or "I'd like a reservation" is booking intent.
- Questions about menu, hours, policies, dietary options, parking, location, etc. are general intent unless the user is clearly booking.
- Extract only information actually supported by the message. Do not invent values.
- If the conversation is already inside a booking flow, "booking" remains appropriate when the user is supplying reservation details.

CURRENT BOOKING STATE:
{current_state}

BOOKING FLOW ACTIVE: {booking_active}

USER MESSAGE:
{message}
"""

    interaction = client.interactions.create(
        model=GEMINI_MODEL,
        input=prompt,
    )

    result = safe_json_from_text(interaction.output_text)

    allowed = {
        "intent",
        "name",
        "email",
        "phone",
        "number_of_guests",
        "date",
        "time",
        "occasion",
        "dietary_requirements",
        "special_requests",
    }

    return {key: result.get(key) for key in allowed}


def rag_tool(query, vector_store):
    """RAG tool: query -> top relevant PDF chunks."""
    if not vector_store:
        return []

    return retrieve_relevant_chunks(
        query=query,
        vector_store=vector_store,
        top_k=TOP_K_RETRIEVAL,
    )


def booking_persistence_tool(booking):
    """Booking persistence tool: structured payload -> booking ID."""
    from db.database import save_booking

    booking_id = save_booking(booking)
    return {"success": True, "booking_id": booking_id}


def booking_retrieval_tool(email=None, phone=None):
    """Booking retrieval tool: customer contact -> matching reservations."""
    from db.database import get_bookings_by_contact

    return get_bookings_by_contact(email=email, phone=phone)


def email_tool(to_email, subject, body):
    """Email tool: to_email/subject/body -> success/failure."""
    from app.email_service import send_email

    return send_email(to_email, subject, body)


def generate_ai_response(user_message, chat_history, vector_store=None):
    """Generate a restaurant-aware answer with recent memory + optional RAG context."""
    client = get_gemini_client()

    relevant_chunks = rag_tool(user_message, vector_store)

    if relevant_chunks:
        context = "\n\n---\n\n".join(relevant_chunks)
    else:
        context = "No restaurant document context was retrieved for this question."

    recent_history = chat_history[-AI_MEMORY_LIMIT:]
    history_text = "\n".join(
        f"{message['role']}: {message['content']}"
        for message in recent_history
    )

    prompt = f"""
You are {RESTAURANT_NAME}'s AI restaurant assistant.

Restaurant description:
{RESTAURANT_DESCRIPTION}

You can:
- answer restaurant questions naturally;
- use uploaded restaurant PDFs when relevant;
- help guests understand reservation-related information.

Rules:
- If the retrieved restaurant documents contain useful information, use it and prioritize it.
- Never invent restaurant-specific facts such as menu items, prices, opening hours, policies, or amenities.
- If the documents do not contain a restaurant-specific fact, say that the knowledge base does not provide it and avoid presenting guesses as facts.
- Do not claim that a table is actually available unless the application has an availability system. This app only records requested reservations.
- Keep responses concise, warm, and professional.
- If the user clearly wants to make a reservation, the booking workflow will handle collection of reservation details.

RECENT CONVERSATION:
{history_text}

RETRIEVED RESTAURANT DOCUMENT CONTEXT:
{context}

LATEST USER MESSAGE:
{user_message}

Respond naturally as the restaurant assistant.
"""

    interaction = client.interactions.create(
        model=GEMINI_MODEL,
        input=prompt,
    )

    return interaction.output_text
