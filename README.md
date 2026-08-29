# 🍽️ BookFlow AI

BookFlow AI is an AI-powered **restaurant reservation assistant** built with Streamlit and Google Gemini.

It combines conversational booking, RAG over uploaded restaurant PDFs, short-term conversation memory, SQLite persistence, email confirmation, and a password-protected admin dashboard.

## Features

- 🤖 Gemini-powered restaurant conversation and intent understanding
- 🍽️ Natural-language table reservation workflow
- 📄 PDF knowledge base with text extraction, chunking, Gemini embeddings, and similarity retrieval
- 🧠 Recent conversation memory (25 messages stored; latest 20 used for AI context)
- 💾 SQLite customer + reservation storage
- 📧 Gmail SMTP confirmation emails
- 🔐 Admin authentication and reservation dashboard
- 📊 Reservation search/filter and CSV export
- ☁️ Streamlit Community Cloud deployment

## Architecture

```text
User
  ↓
Streamlit UI
  ↓
Gemini intent + detail extraction
  ├── Restaurant Q&A → RAG retrieval → Gemini response
  └── Reservation flow → validation → confirmation
                                  ↓
                         SQLite + Email tools
                                  ↓
                           Admin Dashboard
```

## Project Structure

```text
BookFlow-AI/
├── app/
│   ├── main.py
│   ├── chat_logic.py
│   ├── booking_flow.py
│   ├── rag_pipeline.py
│   ├── tools.py
│   ├── email_service.py
│   ├── admin_dashboard.py
│   └── config.py
├── db/
│   └── database.py
├── docs/
├── .streamlit/
│   └── secrets.toml
├── requirements.txt
└── README.md
```

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app/main.py
```

## Secrets

Create `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your_gemini_api_key"
ADMIN_PASSWORD = "your_admin_password"
SENDER_EMAIL = "your_sender_gmail@gmail.com"
SENDER_APP_PASSWORD = "your_gmail_app_password"
```

Never commit `secrets.toml` to GitHub.

## RAG Knowledge Base

Upload one or more restaurant PDFs such as a menu, opening-hours document, cancellation policy, dietary information, or restaurant guide. The system extracts and chunks the text, creates Gemini embeddings, retrieves relevant chunks for a question, and blends that context into the Gemini response.

## Deployment

The Streamlit entry point is:

```text
app/main.py
```

Add the same secret keys through Streamlit Community Cloud's Secrets settings when deploying.

## Note on SQLite

SQLite is used because the assignment permits it. Local/cloud SQLite storage should be treated as demo storage and may reset on Streamlit Cloud restarts or redeployments.
