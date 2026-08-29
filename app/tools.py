import streamlit as st
from google import genai

from app.rag_pipeline import retrieve_relevant_chunks


def get_gemini_client():
    """
    Create a Gemini client using the API key
    stored in Streamlit secrets.
    """

    api_key = st.secrets["GEMINI_API_KEY"]

    return genai.Client(
        api_key=api_key
    )


def rag_tool(query, vector_store):
    """
    Retrieve relevant information from uploaded PDFs.
    """

    if not vector_store:
        return []

    return retrieve_relevant_chunks(
        query=query,
        vector_store=vector_store,
        top_k=3,
    )


def generate_ai_response(
    user_message,
    chat_history,
    vector_store=None,
):
    """
    Generate a Gemini response.

    Uses:
    - Recent conversation history
    - Relevant PDF context
    """

    client = get_gemini_client()

    relevant_chunks = rag_tool(
        user_message,
        vector_store,
    )

    if relevant_chunks:

        context = "\n\n".join(
            relevant_chunks
        )

        context = (
            "Relevant information from uploaded PDFs:\n"
            + context
        )

    else:

        context = (
            "No relevant PDF information was found."
        )


    # Keep recent conversation messages
    recent_history = chat_history[-20:]

    history_text = ""

    for message in recent_history:

        role = message["role"]
        content = message["content"]

        history_text += (
            f"{role}: {content}\n"
        )


    prompt = f"""
You are a helpful AI Booking Assistant.

You can:
1. Answer general questions.
2. Answer questions using uploaded PDF documents.
3. Help users understand booking-related information.

IMPORTANT RULES:
- If information is available in the uploaded PDF context,
  prioritize that information.
- If the PDF context does not contain the answer,
  say that clearly instead of inventing information.
- Be concise and helpful.
- Do not pretend that you have information that was not provided.

CONVERSATION HISTORY:
{history_text}

PDF CONTEXT:
{context}

USER QUESTION:
{user_message}

Answer the user's question:
"""


    interaction = client.interactions.create(
        model="gemini-3.6-flash",
        input=prompt,
    )

    return interaction.output_text