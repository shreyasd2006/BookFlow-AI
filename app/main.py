import sys
import os
from pathlib import Path
from textwrap import dedent

import streamlit as st


# =================================================
# PROJECT ROOT
# =================================================

ROOT_DIR = Path(__file__).resolve().parent.parent

if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


# =================================================
# IMPORT PROJECT MODULES
# =================================================

from app.chat_logic import (
    detect_intent,
    generate_general_response,
)

from app.booking_flow import (
    create_empty_booking,
    get_missing_fields,
    get_next_question,
    update_booking_field,
    format_booking_summary,
)

from app.admin_dashboard import (
    show_admin_dashboard,
)

from app.rag_pipeline import (
    extract_text_from_pdf,
    chunk_text,
    create_vector_store,
)

from db.database import (
    initialize_database,
    save_booking,
)

from app.email_service import (
    send_booking_confirmation,
)


# =================================================
# PAGE CONFIG
# =================================================

st.set_page_config(
    page_title="BookFlow AI",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =================================================
# CUSTOM CSS
# =================================================

st.markdown(
    dedent(
        """
        <style>

        .stApp {
            background-color: #0e1117;
        }

        .block-container {
            max-width: 1200px;
            padding-top: 2rem;
            padding-bottom: 2rem;
        }

        section[data-testid="stSidebar"] {
            border-right: 1px solid rgba(255,255,255,0.08);
        }

        .stButton > button {
            border-radius: 10px;
            font-weight: 600;
        }

        .stTextInput input {
            border-radius: 10px;
        }

        div[data-testid="stMetric"] {
            background-color: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.08);
            padding: 1rem;
            border-radius: 14px;
        }

        [data-testid="stChatMessage"] {
            border-radius: 14px;
        }

        footer {
            visibility: hidden;
        }

        </style>
        """
    ),
    unsafe_allow_html=True,
)


# =================================================
# DATABASE INITIALIZATION
# =================================================

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
# GET ADMIN PASSWORD
# =================================================

def get_admin_password():

    # Try different possible names from secrets.toml
    possible_secret_keys = [
        "ADMIN_PASSWORD",
        "admin_password",
        "Admin_Password",
        "ADMIN_PWD",
        "admin_pwd",
        "PASSWORD",
    ]

    for key in possible_secret_keys:

        try:

            if key in st.secrets:
                return str(st.secrets[key])

        except Exception:
            pass


    # Try environment variables as fallback
    possible_env_keys = [
        "ADMIN_PASSWORD",
        "admin_password",
        "ADMIN_PWD",
        "admin_pwd",
    ]

    for key in possible_env_keys:

        value = os.getenv(key)

        if value:
            return value


    return None


# =================================================
# SIDEBAR
# =================================================

with st.sidebar:

    st.title("✨ BookFlow AI")

    st.caption(
        "Intelligent bookings, powered by AI"
    )

    st.divider()


    page = st.radio(
        "Navigation",
        [
            "💬 AI Assistant",
            "🔐 Admin Dashboard",
        ],
        label_visibility="collapsed",
    )


    st.divider()


    # ---------------------------------------------
    # KNOWLEDGE BASE
    # ---------------------------------------------

    st.subheader("📚 Knowledge Base")

    st.caption(
        "Upload PDFs to give your AI assistant "
        "additional context."
    )


    uploaded_files = st.file_uploader(
        "Upload PDF documents",
        type=["pdf"],
        accept_multiple_files=True,
    )


    if st.button(
        "⚡ Process Knowledge Base",
        width="stretch",
    ):

        if not uploaded_files:

            st.warning(
                "Please upload at least one PDF."
            )

        else:

            try:

                all_chunks = []

                with st.spinner(
                    "Processing your documents..."
                ):

                    for uploaded_file in uploaded_files:

                        text = extract_text_from_pdf(
                            uploaded_file
                        )

                        if text and text.strip():

                            chunks = chunk_text(
                                text
                            )

                            all_chunks.extend(
                                chunks
                            )


                    if not all_chunks:

                        st.error(
                            "No readable text was found "
                            "in the uploaded PDFs."
                        )

                    else:

                        st.session_state.vector_store = (
                            create_vector_store(
                                all_chunks
                            )
                        )

                        st.success(
                            f"Successfully processed "
                            f"{len(all_chunks)} text chunks!"
                        )


            except Exception as error:

                st.error(
                    f"Error processing PDFs: {error}"
                )


    # ---------------------------------------------
    # KNOWLEDGE STATUS
    # ---------------------------------------------

    if st.session_state.vector_store is not None:

        st.success(
            "🟢 Knowledge Base Active"
        )

    else:

        st.caption(
            "⚪ No documents loaded"
        )


    st.divider()


    # ---------------------------------------------
    # NEW CHAT
    # ---------------------------------------------

    if st.button(
        "🗑️ Start New Conversation",
        width="stretch",
    ):

        st.session_state.messages = []

        st.session_state.booking = (
            create_empty_booking()
        )

        st.session_state.booking_active = False

        st.session_state.awaiting_confirmation = (
            False
        )

        st.rerun()


    st.divider()

    st.caption(
        "🤖 Gemini-powered assistant"
    )


# =================================================
# ADMIN DASHBOARD
# =================================================

if page == "🔐 Admin Dashboard":

    st.title("🔐 Admin Dashboard")

    st.caption(
        "Secure access to booking information"
    )

    st.divider()


    if not st.session_state.admin_authenticated:

        login_col1, login_col2, login_col3 = (
            st.columns([1, 2, 1])
        )


        with login_col2:

            with st.container(border=True):

                st.markdown("### 🔐 Admin Access")

                st.caption(
                    "Enter your administrator password "
                    "to access booking information."
                )


                admin_password = st.text_input(
                    "Admin password",
                    type="password",
                    placeholder="Enter your password",
                )


                if st.button(
                    "Unlock Dashboard",
                    type="primary",
                    width="stretch",
                ):

                    correct_password = (
                        get_admin_password()
                    )


                    if not correct_password:

                        st.error(
                            "Admin password is not configured. "
                            "The app could not find the password "
                            "in Streamlit secrets."
                        )

                    elif admin_password == correct_password:

                        st.session_state.admin_authenticated = (
                            True
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Incorrect password."
                        )


        st.stop()


    # ---------------------------------------------
    # LOGGED IN ADMIN
    # ---------------------------------------------

    header_col, logout_col = st.columns(
        [6, 1]
    )


    with header_col:

        st.caption(
            "Manage and monitor customer bookings."
        )


    with logout_col:

        if st.button(
            "Logout",
            width="stretch",
        ):

            st.session_state.admin_authenticated = (
                False
            )

            st.rerun()


    st.divider()


    show_admin_dashboard()

    st.stop()


# =================================================
# MAIN AI ASSISTANT PAGE
# =================================================

st.title("Your Intelligent Booking Assistant")

st.caption(
    "Ask questions, create bookings, or upload "
    "documents and ask questions about them."
)


# =================================================
# HERO / FEATURE SECTION
# =================================================

if not st.session_state.messages:

    st.divider()


    col1, col2, col3 = st.columns(3)


    with col1:

        with st.container(border=True):

            st.markdown("## 📅")

            st.markdown(
                "### Create a Booking"
            )

            st.caption(
                "Tell me what you need and I will "
                "guide you through the booking process."
            )


    with col2:

        with st.container(border=True):

            st.markdown("## 📄")

            st.markdown(
                "### Ask Your Documents"
            )

            st.caption(
                "Upload PDF documents and ask questions "
                "using information from them."
            )


    with col3:

        with st.container(border=True):

            st.markdown("## 🧠")

            st.markdown(
                "### Context Aware"
            )

            st.caption(
                "The assistant remembers recent "
                "conversation context for better "
                "follow-up responses."
            )


    st.divider()


# =================================================
# CHAT HISTORY
# =================================================

for message in st.session_state.messages:

    with st.chat_message(
        message["role"]
    ):

        st.markdown(
            message["content"]
        )


# =================================================
# CHAT INPUT
# =================================================

user_input = st.chat_input(
    "Message BookFlow AI..."
)


if user_input:

    # ---------------------------------------------
    # SHOW USER MESSAGE
    # ---------------------------------------------

    with st.chat_message("user"):

        st.markdown(
            user_input
        )


    # ---------------------------------------------
    # SAVE USER MESSAGE
    # ---------------------------------------------

    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
        }
    )


    # =================================================
    # BOOKING CONFIRMATION
    # =================================================

    if st.session_state.awaiting_confirmation:

        response = (
            user_input
            .strip()
            .lower()
        )


        if response in [
            "yes",
            "y",
            "confirm",
        ]:

            try:

                booking_id = save_booking(
                    st.session_state.booking
                )


                email_sent, email_message = (
                    send_booking_confirmation(
                        st.session_state.booking,
                        booking_id,
                    )
                )


                if email_sent:

                    bot_response = (
                        "## 🎉 Booking Confirmed!\n\n"
                        f"Your **Booking ID is #{booking_id}**.\n\n"
                        "Your booking has been saved successfully "
                        "and a confirmation email has been sent to "
                        f"**{st.session_state.booking['email']}**."
                    )

                else:

                    bot_response = (
                        "## 🎉 Booking Confirmed!\n\n"
                        f"Your **Booking ID is #{booking_id}**.\n\n"
                        "Your booking was saved successfully. "
                        "However, the confirmation email could "
                        "not be sent."
                    )


                st.session_state.booking = (
                    create_empty_booking()
                )

                st.session_state.booking_active = False

                st.session_state.awaiting_confirmation = (
                    False
                )


            except Exception as error:

                bot_response = (
                    "❌ Something went wrong while saving "
                    "your booking."
                )


        elif response in [
            "no",
            "n",
            "cancel",
        ]:

            bot_response = (
                "❌ Your booking has been cancelled. "
                "No information was saved."
            )


            st.session_state.booking = (
                create_empty_booking()
            )

            st.session_state.booking_active = False

            st.session_state.awaiting_confirmation = (
                False
            )


        else:

            bot_response = (
                "Please reply **YES** to confirm your booking "
                "or **NO** to cancel it."
            )


    # =================================================
    # ACTIVE BOOKING FLOW
    # =================================================

    elif st.session_state.booking_active:

        missing_fields = get_missing_fields(
            st.session_state.booking
        )


        current_field = missing_fields[0]


        success, message = update_booking_field(
            st.session_state.booking,
            current_field,
            user_input,
        )


        if not success:

            bot_response = message


        else:

            missing_fields = get_missing_fields(
                st.session_state.booking
            )


            if missing_fields:

                bot_response = get_next_question(
                    st.session_state.booking
                )


            else:

                bot_response = format_booking_summary(
                    st.session_state.booking
                )

                st.session_state.awaiting_confirmation = (
                    True
                )


    # =================================================
    # NEW REQUEST
    # =================================================

    else:

        intent = detect_intent(
            user_input
        )


        # ---------------------------------------------
        # BOOKING INTENT
        # ---------------------------------------------

        if intent == "booking":

            st.session_state.booking_active = True


            bot_response = (
                "Absolutely! 📅 Let's get your booking "
                "set up.\n\n"
                +
                get_next_question(
                    st.session_state.booking
                )
            )


        # ---------------------------------------------
        # GENERAL / RAG QUESTION
        # ---------------------------------------------

        else:

            try:

                with st.spinner(
                    "BookFlow AI is thinking..."
                ):

                    bot_response = (
                        generate_general_response(
                            message=user_input,
                            chat_history=(
                                st.session_state.messages
                            ),
                            vector_store=(
                                st.session_state.vector_store
                            ),
                        )
                    )


            except Exception as error:

                bot_response = (
                    "⚠️ I couldn't generate a response "
                    "right now. Please try again."
                )


    # =================================================
    # SHOW ASSISTANT RESPONSE
    # =================================================

    with st.chat_message("assistant"):

        st.markdown(
            bot_response
        )


    # =================================================
    # SAVE ASSISTANT RESPONSE
    # =================================================

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": bot_response,
        }
    )


    # =================================================
    # KEEP LAST 25 MESSAGES
    # =================================================

    if len(
        st.session_state.messages
    ) > 25:

        st.session_state.messages = (
            st.session_state.messages[-25:]
        )