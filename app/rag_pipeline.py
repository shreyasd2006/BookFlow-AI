import streamlit as st
import numpy as np
from pypdf import PdfReader
from google import genai


def get_gemini_client():
    """
    Create Gemini client using the API key
    stored in Streamlit secrets.
    """

    return genai.Client(
        api_key=st.secrets["GEMINI_API_KEY"]
    )


def extract_text_from_pdf(uploaded_file):
    """
    Extract text from an uploaded PDF.
    """

    reader = PdfReader(uploaded_file)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:

            text += page_text + "\n"

    return text


def chunk_text(
    text,
    chunk_size=800,
    overlap=150,
):
    """
    Split PDF text into overlapping chunks.
    """

    chunks = []

    start = 0

    while start < len(text):

        end = start + chunk_size

        chunk = text[start:end]

        chunks.append(chunk)

        start += (
            chunk_size - overlap
        )

    return chunks


def create_embedding(text):
    """
    Create an embedding using Gemini.
    """

    client = get_gemini_client()

    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
    )

    return np.array(
        response.embeddings[0].values
    )


def create_vector_store(chunks):
    """
    Create embeddings for all PDF chunks.
    """

    embeddings = []

    for chunk in chunks:

        embedding = create_embedding(
            chunk
        )

        embeddings.append(
            embedding
        )

    return {
        "chunks": chunks,
        "embeddings": np.array(
            embeddings
        ),
    }


def cosine_similarity(
    vector_a,
    vector_b,
):
    """
    Calculate cosine similarity manually.
    """

    denominator = (
        np.linalg.norm(vector_a)
        *
        np.linalg.norm(vector_b)
    )

    if denominator == 0:

        return 0

    return np.dot(
        vector_a,
        vector_b,
    ) / denominator


def retrieve_relevant_chunks(
    query,
    vector_store,
    top_k=3,
):
    """
    Retrieve the most relevant PDF chunks
    for a user question.
    """

    if not vector_store:

        return []


    query_embedding = create_embedding(
        query
    )


    similarities = []


    for chunk_embedding in (
        vector_store["embeddings"]
    ):

        similarity = cosine_similarity(
            query_embedding,
            chunk_embedding,
        )

        similarities.append(
            similarity
        )


    top_indices = np.argsort(
        similarities
    )[-top_k:][::-1]


    return [
        vector_store["chunks"][index]
        for index in top_indices
    ]