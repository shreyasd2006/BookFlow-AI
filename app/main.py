import os
import sys
from pathlib import Path

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.admin_dashboard import show_admin_dashboard
from app.booking_flow import (
    create_empty_booking,
    format_booking_summary,
    get_missing_fields,
    get_next_question,
    merge_extracted_details,
    update_booking_field,
)
from app.chat_logic import analyze_message, generate_general_response
from app.config import MEMORY_LIMIT, RESTAURANT_DESCRIPTION, RESTAURANT_NAME, RESTAURANT_TAGLINE
from app.email_service import send_booking_confirmation
from app.rag_pipeline import create_vector_store, chunk_text, extract_text_from_pdf
from db.database import initialize_database
from app.tools import booking_persistence_tool


st.set_page_config(
    page_title=f"{RESTAURANT_NAME} · BookFlow AI",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =================================================
# UI STYLING
# =================================================

st.markdown(
    """
    <style>
        .block-container {
            max-width: 1180px;
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(128,128,128,0.18);
        }

        .restaurant-hero {
            padding: 2rem 2.2rem;
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(180,118,52,.18), rgba(114,82,50,.08));
            border: 1px solid rgba(180,118,52,.25);
            margin-bottom: 1.4rem;
        }

        .eyebrow {
            font-size: .78rem;
            font-weight: 700;
            letter-spacing: .12em;
            text-transform: uppercase;
            opacity: .65;
        }

        .hero-title {
            font-size: 2.35rem;
            line-height: 1.1;
            font-weight: 800;
            margin-top: .35rem;
        }

        .hero-copy {
            max-width: 760px;
            opacity: .72;
            margin-top: .55rem;
            line-height: 1.55;
        }

        .status-pill {
            display: inline-block;
            padding: .3rem .7rem;
            border-radius: 999px;
            background: rgba(46,160,67,.12);
            border: 1px solid rgba(46,160,67,.25);
            color: #3fb950;
            font-size: .78rem;
            font-weight: 700;
        }

        .feature-note {
            min-height: 130px;
        }

        .sidebar-brand {
            font-size: 1.45rem;
            font-weight: 800;
            margin-bottom: .15rem;
        }

        .sidebar-tagline {
            opacity: .62;
            font-size: .82rem;
            line-height: 1.4;
        }

        .stButton > button {
            border-radius: 10px;
            font-weight: 650;
        }

        [data-testid="stChatMessage"] {
            border-radius: 14px;
        }

        footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)


initialize_database()


# =================================================
# SESSION STATE
# =================================================

if "messages" not in st.session_state:
    st.session_state.messages = []

if "booking" not in st.session_state:
    st.session_state.booking = create_empty_booking()

if "booking_active" not in st.session_state:
    st.session_state.booking_active = False

if "awaiting_confirmation" not in st.session_state:
    st.session_state.awaiting_confirmation = False

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None

if "admin_authenticated" not in st.session_state:
    st.session_state.admin_authenticated = False


# =================================================
# ADMIN PASSWORD
# =================================================

def get_admin_password():
    for key in ["ADMIN_PASSWORD", "admin_password", "ADMIN_PWD"]:
        try:
            if key in st.secrets:
                return str(st.secrets[key])
        except Exception:
            pass

    return os.getenv("ADMIN_PASSWORD")


# =================================================
# SIDEBAR
# =================================================

with st.sidebar:
    st.markdown(
        f'<div class="sidebar-brand">🍽️ {RESTAURANT_NAME}</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="sidebar-tagline">{RESTAURANT_TAGLINE}<br>Powered by BookFlow AI</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    page = st.radio(
        "Workspace",
        ["💬 Guest Assistant", "🔐 Admin Dashboard"],
        label_visibility="collapsed",
    )

    st.divider()

    st.subheader("📚 Restaurant Knowledge")
    st.caption(
        "Upload menus, policies, opening hours, dietary information, or other restaurant PDFs."
    )

    uploaded_files = st.file_uploader(
        "Restaurant PDFs",
        type=["pdf"],
        accept_multiple_files=True,
    )

    if st.button("⚡ Process Knowledge Base", width="stretch"):
        if not uploaded_files:
            st.warning("Please upload at least one restaurant PDF.")
        else:
            try:
                all_chunks = []
                with st.spinner("Reading and indexing restaurant documents..."):
                    for uploaded_file in uploaded_files:
                        text = extract_text_from_pdf(uploaded_file)
                        if text.strip():
                            all_chunks.extend(chunk_text(text))

                if not all_chunks:
                    st.error("No readable text was found in the uploaded PDFs.")
                else:
                    st.session_state.vector_store = create_vector_store(all_chunks)
                    st.success(f"Knowledge base ready · {len(all_chunks)} chunks indexed")
            except Exception:
                st.error("The PDF could not be processed. Please try another text-based PDF.")

    if st.session_state.vector_store:
        st.success("🟢 Restaurant knowledge active")
    else:
        st.caption("⚪ No restaurant documents loaded")

    st.divider()

    if st.button("🗑️ Start New Conversation", width="stretch"):
        st.session_state.messages = []
        st.session_state.booking = create_empty_booking()
        st.session_state.booking_active = False
        st.session_state.awaiting_confirmation = False
        st.rerun()


# =================================================
# ADMIN PAGE
# =================================================

if page == "🔐 Admin Dashboard":
    st.title("🔐 Restaurant Admin Dashboard")
    st.caption("Secure access to reservation information")

    if not st.session_state.admin_authenticated:
        with st.container(border=True):
            st.subheader("Admin Access")
            st.caption("Enter the administrator password to continue.")

            admin_password = st.text_input(
                "Admin password",
                type="password",
                placeholder="Enter password",
            )

            if st.button("Unlock Dashboard", type="primary", width="stretch"):
                correct_password = get_admin_password()

                if not correct_password:
                    st.error("Admin password is not configured in secrets.")
                elif admin_password == correct_password:
                    st.session_state.admin_authenticated = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")

        st.stop()

    left, right = st.columns([6, 1])
    with left:
        st.caption("Monitor and search restaurant reservations.")
    with right:
        if st.button("Logout", width="stretch"):
            st.session_state.admin_authenticated = False
            st.rerun()

    st.divider()
    show_admin_dashboard()
    st.stop()


# =================================================
# GUEST PAGE
# =================================================

st.markdown(
    f"""
    <div class="restaurant-hero">
        <div class="status-pill">● AI ASSISTANT ONLINE</div>
        <div class="eyebrow">{RESTAURANT_NAME}</div>
        <div class="hero-title">Your table, sorted. 🍽️</div>
        <div class="hero-copy">
            {RESTAURANT_DESCRIPTION}
            Ask about the restaurant, upload a document, or tell me naturally that you'd like a table.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


if not st.session_state.messages:
    c1, c2, c3 = st.columns(3)

    with c1:
        with st.container(border=True):
            st.markdown("## 🍽️")
            st.markdown("### Reserve a Table")
            st.caption("Try: “Book dinner for 4 tomorrow at 8 PM.”")

    with c2:
        with st.container(border=True):
            st.markdown("## 📄")
            st.markdown("### Ask the Restaurant")
            st.caption("Upload a menu or policy PDF and ask questions about it.")

    with c3:
        with st.container(border=True):
            st.markdown("## 🧠")
            st.markdown("### Context Aware")
            st.caption("The assistant uses recent conversation context for follow-ups.")

    st.divider()


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


user_input = st.chat_input("Message the restaurant assistant...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)

    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
    })

    # ---------------------------------------------
    # CONFIRMATION
    # ---------------------------------------------
    if st.session_state.awaiting_confirmation:
        response = user_input.strip().lower()

        if response in {"yes", "y", "confirm"}:
            try:
                result = booking_persistence_tool(st.session_state.booking)
                booking_id = result["booking_id"]

                email_sent, _email_message = send_booking_confirmation(
                    st.session_state.booking,
                    booking_id,
                )

                if email_sent:
                    bot_response = (
                        "## 🎉 Reservation Confirmed\n\n"
                        f"Your reservation ID is **#{booking_id}**.\n\n"
                        "A confirmation email has been sent to "
                        f"**{st.session_state.booking['email']}**."
                    )
                else:
                    bot_response = (
                        "## ✅ Reservation Confirmed\n\n"
                        f"Your reservation ID is **#{booking_id}**.\n\n"
                        "Your reservation was saved successfully, but the confirmation email could not be sent."
                    )

                st.session_state.booking = create_empty_booking()
                st.session_state.booking_active = False
                st.session_state.awaiting_confirmation = False

            except Exception:
                bot_response = (
                    "❌ I couldn't complete the reservation right now. "
                    "Please try confirming again."
                )

        elif response in {"no", "n", "cancel"}:
            bot_response = (
                "No problem — the reservation was cancelled and nothing was saved."
            )
            st.session_state.booking = create_empty_booking()
            st.session_state.booking_active = False
            st.session_state.awaiting_confirmation = False

        else:
            bot_response = "Please reply **YES** to confirm or **NO** to cancel."

    # ---------------------------------------------
    # BOOKING / GEMINI EXTRACTION
    # ---------------------------------------------
    else:
        try:
            analysis = analyze_message(
                user_input,
                st.session_state.booking,
                st.session_state.booking_active,
            )
        except Exception:
            analysis = {
                "intent": "unclear",
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

        intent = analysis.get("intent", "unclear")

        if intent == "booking" or st.session_state.booking_active:
            st.session_state.booking_active = True

            # Extract everything Gemini understood from this message.
            merge_extracted_details(
                st.session_state.booking,
                analysis,
            )

            # Validate extracted required details that are present.
            validation_message = None
            for field in [
                "name",
                "email",
                "phone",
                "number_of_guests",
                "date",
                "time",
            ]:
                value = st.session_state.booking.get(field)
                if not value:
                    continue

                candidate = str(value)
                check_booking = dict(st.session_state.booking)
                check_booking[field] = None
                success, message = update_booking_field(
                    check_booking,
                    field,
                    candidate,
                )
                if not success:
                    st.session_state.booking[field] = None
                    validation_message = message
                    break

            if validation_message:
                bot_response = validation_message
            else:
                missing = get_missing_fields(st.session_state.booking)

                if missing:
                    bot_response = get_next_question(st.session_state.booking)
                else:
                    bot_response = format_booking_summary(
                        st.session_state.booking
                    )
                    st.session_state.awaiting_confirmation = True

        else:
            try:
                with st.spinner("Thinking..."):
                    bot_response = generate_general_response(
                        message=user_input,
                        chat_history=st.session_state.messages,
                        vector_store=st.session_state.vector_store,
                    )
            except Exception:
                bot_response = (
                    "⚠️ I couldn't generate a response right now. Please try again in a moment."
                )

    with st.chat_message("assistant"):
        st.markdown(bot_response)

    st.session_state.messages.append({
        "role": "assistant",
        "content": bot_response,
    })

    if len(st.session_state.messages) > MEMORY_LIMIT:
        st.session_state.messages = st.session_state.messages[-MEMORY_LIMIT:]
