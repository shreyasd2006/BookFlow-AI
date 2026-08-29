import streamlit as st
import numpy as np
from pypdf import PdfReader
from google import genai

from app.config import EMBEDDING_MODEL


def get_gemini_client():
    return genai.Client(api_key=st.secrets["GEMINI_API_KEY"])


def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)
    text_parts = []

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_parts.append(page_text)

    return "\n\n".join(text_parts)


def chunk_text(text, chunk_size=800, overlap=150):
    chunks = []
    start = 0
    step = max(1, chunk_size - overlap)

    while start < len(text):
        chunk = text[start : start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        start += step

    return chunks


def create_embedding(text):
    client = get_gemini_client()
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )
    return np.array(response.embeddings[0].values, dtype=float)


def create_vector_store(chunks):
    if not chunks:
        return None

    embeddings = [create_embedding(chunk) for chunk in chunks]

    return {
        "chunks": chunks,
        "embeddings": np.array(embeddings),
    }


def cosine_similarity(vector_a, vector_b):
    denominator = np.linalg.norm(vector_a) * np.linalg.norm(vector_b)
    if denominator == 0:
        return 0.0
    return float(np.dot(vector_a, vector_b) / denominator)


def retrieve_relevant_chunks(query, vector_store, top_k=3):
    if not vector_store:
        return []

    query_embedding = create_embedding(query)

    scores = [
        cosine_similarity(query_embedding, embedding)
        for embedding in vector_store["embeddings"]
    ]

    top_indices = np.argsort(scores)[-top_k:][::-1]
    return [vector_store["chunks"][index] for index in top_indices]
