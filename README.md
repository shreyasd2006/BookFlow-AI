# ✨ BookFlow AI

> An intelligent, AI-powered booking assistant with conversational booking flows, document-aware answers, recent conversation memory, and an admin dashboard.

## 🚀 Overview

BookFlow AI allows users to interact with an AI assistant to:

- 📅 Create and manage bookings through natural conversation
- 📄 Upload PDF documents as a knowledge base
- 🧠 Ask questions using information extracted from uploaded documents
- 💬 Maintain recent conversation context for follow-up questions
- 📧 Send booking-related email notifications
- 🔐 Securely access an admin dashboard
- 📊 View and manage stored booking information

The application uses **Google Gemini** for AI responses and runs with a **Streamlit** frontend.

---

## ✨ Key Features

### 🤖 AI Booking Assistant
Users can describe what they need in natural language. The assistant collects the required booking details and guides them through the booking process conversationally.

### 📚 PDF Knowledge Base
PDF documents can be uploaded and processed into text chunks. Relevant document content is retrieved and provided to the AI when answering document-related questions.

### 🧠 Conversation Memory
The assistant keeps recent conversation history in memory so that follow-up questions can be understood in context.

### 📧 Email Notifications
The application includes an email service for sending booking-related notifications when configured.

### 🔐 Admin Dashboard
The dashboard is protected using an admin password stored securely in Streamlit secrets. It provides access to booking information and management features.

### 💾 SQLite Database
Bookings are stored locally using SQLite, making the project simple to run and deploy without requiring an external database.

---

## 🛠️ Tech Stack

- **Python**
- **Streamlit**
- **Google Gemini API**
- **Hugging Face / Sentence Transformers** for embeddings
- **FAISS** for similarity search
- **PyPDF** for PDF text extraction
- **SQLite**
- **GitHub**
- **Streamlit Community Cloud**

---

## 📁 Project Structure

```text
AI_Chatbot/
│
├── .streamlit/
│   └── secrets.toml
│
├── app/
│   ├── main.py
│   ├── chat_logic.py
│   ├── booking_flow.py
│   ├── rag_pipeline.py
│   ├── admin_dashboard.py
│   ├── database.py
│   ├── email_service.py
│   ├── config.py
│   └── tools.py
│
├── db/
│   ├── __init__.py
│   └── database.py
│
├── docs/
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚙️ Local Setup

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd AI_Chatbot
```

### 2. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Streamlit secrets

Create:

```text
.streamlit/secrets.toml
```

Example:

```toml
GEMINI_API_KEY = "your_gemini_api_key"
ADMIN_PASSWORD = "your_admin_password"
```

Add any additional email-related secrets required by your configuration.

> Never commit `secrets.toml` to GitHub.

### 5. Run the application

From the project root:

```powershell
streamlit run app/main.py
```

Open the local URL shown in the terminal.

---

## 📄 Using the Knowledge Base

1. Open the AI Assistant.
2. Upload one or more PDF files.
3. Click **Process Knowledge Base**.
4. Wait for the PDFs to be converted into searchable text chunks.
5. Ask questions related to the uploaded documents.

The assistant retrieves relevant chunks before generating its response.

---

## 🔐 Admin Dashboard

The Admin Dashboard is protected with the password stored in:

```text
.streamlit/secrets.toml
```

Example:

```toml
ADMIN_PASSWORD = "your_secure_password"
```

Do not hard-code the password directly inside the Python source code.

---

## 🌐 Deployment

The project can be deployed using **Streamlit Community Cloud**:

1. Push the project to GitHub.
2. Create a new Streamlit Community Cloud application.
3. Select the repository and set the entry point to:

```text
app/main.py
```

4. Add the required values from `secrets.toml` through the deployment platform's secrets configuration.
5. Deploy.

---

## 🔒 Security Notes

- API keys and passwords are stored outside the source code.
- `.streamlit/secrets.toml` should remain in `.gitignore`.
- The admin dashboard requires password authentication.
- Uploaded documents are processed for retrieval-based answering.

---

## 🎯 Project Highlights

BookFlow AI combines several AI application concepts in one project:

- Conversational AI
- Tool-assisted booking workflows
- Retrieval-Augmented Generation (RAG)
- PDF knowledge retrieval
- Conversation memory
- Secure secret handling
- Database-backed booking storage
- Cloud deployment

---

## 📌 Future Improvements

- User authentication
- Persistent user-specific chat history
- Booking cancellation and modification flows
- External calendar integration
- Cloud database migration
- Analytics and reporting
- Role-based admin access

---

## 👨‍💻 Author

Built as an AI-powered booking assistant project using Python, Streamlit, Gemini, RAG, and SQLite.
