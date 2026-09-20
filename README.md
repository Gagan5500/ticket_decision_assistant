# Minimal AI Support Decision API & Streamlit Assistant

An end-to-end AI-powered support-ticket decision assistant built with **Python 3.12**, **FastAPI**, **SQLite**, **JWT Authentication & Authorization**, **RAG (Retrieval-Augmented Generation)**, and **Streamlit**.

---

## 🌟 Key Features

1. **FastAPI REST API**: High-performance backend providing endpoints for authentication, ticket processing, and history.
2. **JWT Authentication & Multi-Tenant Authorization**:
   - Secure password hashing using bcrypt.
   - JWT tokens issued on login (`Authorization: Bearer <token>`).
   - Strict multi-tenant isolation (e.g. Alice's token cannot retrieve Bob's tickets).
3. **SQLite Database with Foreign Key Integrity**:
   - Stores `users`, `tickets`, and `decisions` with relational integrity.
4. **Local RAG Pipeline & CAG**:
   - Ingests policy documents (`damaged_goods.md`, `refunds.md`, `returns.md`, `shipping.md`).
   - Local chunking and TF-IDF / Cosine similarity scoring (NumPy) with zero external vector database overhead.
5. **Structured AI Decision Engine**:
   - Grounded LLM output strictly matching the schema: `action`, `confidence`, `reason`, and `sources`.
   - Built-in guardrails that return `NEEDS_MORE_INFORMATION` when tickets lack sufficient details.
   - Powered by **Google Gemini API** (`gemini-2.5-flash`), with an offline deterministic fallback.
6. **Streamlit Frontend**:
   - Pure HTTP client communicating with the FastAPI backend.
   - Interactive views: Login/Register, New Ticket Submission with sample presets, and Decision History inspection.
7. **Evaluation Benchmark Runner**:
   - Automated runner testing against `data/tickets.csv` and printing accuracy metrics.

---

## 📐 Architecture

```text
 ┌─────────────────────────────────────────────────────────────┐
 │                      Streamlit Frontend                     │
 │          (Login / Register, New Decision, History)          │
 └──────────────────────────────┬──────────────────────────────┘
                                │ HTTP (Bearer JWT)
                                ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                       FastAPI Backend                       │
 │      • Auth & Tenant Isolation Check (/register, /login)    │
 │      • Ticket Processing & Querying (/tickets, /tickets/id) │
 └──────────────┬──────────────────────────────┬───────────────┘
                │                              │
                ▼                              ▼
 ┌─────────────────────────────┐ ┌─────────────────────────────┐
 │       SQLite Database       │ │    RAG & Decision Engine    │
 │  • users                    │ │  • Local Policy Chunks      │
 │  • tickets                  │ │  • TF-IDF / Cosine Scoring  │
 │  • decisions                │ │  • Gemini 2.5 Flash LLM     │
 └─────────────────────────────┘ └─────────────────────────────┘
```

---

## 📁 Repository Structure

```text
.
├── README.md                 # Setup, architecture, and API documentation
├── DEVELOPMENT.md            # AI coding agent workflow and design decisions
├── requirements.txt          # Python package dependencies
├── .env.example              # Environment variable template
├── .gitignore                # Git ignore configuration
├── data/
│   └── tickets.csv           # Benchmark test cases for evaluation
├── knowledge_base/
│   ├── damaged_goods.md      # Damaged goods policy (₹2,000 photo rule)
│   ├── refunds.md            # Refund timelines and cancellation rules
│   ├── returns.md            # 7-day return policy and non-returnables
│   └── shipping.md           # Transit SLAs, lost packages, and reroutes
├── src/
│   ├── __init__.py
│   ├── api.py                # FastAPI REST API endpoints
│   ├── auth.py               # Password hashing & JWT verification
│   ├── database.py           # SQLite database schema and CRUD operations
│   ├── decision.py           # Structured decision engine & Gemini caller
│   ├── evaluate.py           # Benchmark evaluation runner
│   └── retrieval.py          # Local RAG chunking and similarity retrieval
├── streamlit_app.py          # Streamlit UI frontend
└── tests/
    ├── test_auth.py          # Registration, login, and token tests
    ├── test_isolation.py     # Multi-tenant security tests (Alice vs Bob)
    └── test_rag_decision.py  # Retrieval and decision engine unit tests
```

---

## 🗄️ Database Schema

### `users`
- `id` (INTEGER, Primary Key, Autoincrement)
- `email` (TEXT, Unique, Indexed)
- `password_hash` (TEXT)
- `created_at` (TIMESTAMP)

### `tickets`
- `id` (INTEGER, Primary Key, Autoincrement)
- `user_id` (INTEGER, Foreign Key -> `users.id`)
- `message` (TEXT)
- `created_at` (TIMESTAMP)

### `decisions`
- `id` (INTEGER, Primary Key, Autoincrement)
- `ticket_id` (INTEGER, Foreign Key -> `tickets.id`, Unique)
- `action` (TEXT) — e.g., `REQUEST_PHOTOS`, `APPROVE_REFUND`
- `reason` (TEXT) — Grounded policy explanation
- `confidence` (REAL) — Confidence score (0.0 to 1.0)
- `sources` (TEXT / JSON) — Citing policy files
- `created_at` (TIMESTAMP)

---

## 🚀 Quickstart & Installation

### 1. Prerequisites
- Python 3.10+ (Python 3.12 recommended)
- Git

### 2. Set Up Virtual Environment

**Windows:**
```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` to supply your credentials:
```ini
GEMINI_API_KEY=your_gemini_api_key_here
JWT_SECRET=b6f5d8102d84c31f476a6a9efc7e49e29a67e452140bbd0891
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=120
DATABASE_URL=sqlite:///./app.db
API_BASE_URL=http://127.0.0.1:8000
```
*(Note: If `GEMINI_API_KEY` is not set, the built-in grounded rule engine ensures full local functionality and testing).*

---

## 🏃 Running the Application

### 1. Start the FastAPI Backend
```bash
uvicorn src.api:app --reload --port 8000
```
- API will be accessible at: `http://127.0.0.1:8000`
- Interactive Swagger UI: `http://127.0.0.1:8000/docs`

### 2. Start the Streamlit Frontend (In a separate terminal)
```bash
streamlit run streamlit_app.py
```
- Streamlit will open at: `http://localhost:8501`

### 3. Or 1-Click Run via VS Code (F5)
Pre-configured VS Code debug profiles are available in `.vscode/launch.json`:
1. Press `Ctrl + Shift + D` to open the **Run and Debug** view.
2. Select **`1. Run FastAPI Backend`** and press `F5`.
3. Select **`2. Run Streamlit App`** and press `F5`.

---

## 🧪 Running Automated Tests

Run the complete test suite:
```bash
pytest tests/ -v
```

This validates:
- User registration and duplicate prevention
- Password hashing and JWT generation
- `/me` protected route authorization
- **Tenant Isolation**: Alice cannot access Bob's tickets (returns 403 Forbidden)
- RAG retrieval accuracy and structured decision parsing

---

## 📊 Running the Evaluation Runner

To run the system against the 10 benchmark test cases in `data/tickets.csv`:
```bash
python -m src.evaluate
```

Sample output:
```text
================================================================================
RUNNING AI DECISION EVALUATION BENCHMARK
Dataset: data/tickets.csv | Cases: 10
================================================================================
[PASS] Ticket #1
   Message:   I bought a luxury leather jacket for ₹4,500 (Order #9821)...
   Expected:  REQUEST_PHOTOS
   Predicted: REQUEST_PHOTOS (conf: 0.92)
   Reason:    The order is ₹4,500 (above the ₹2,000 threshold) and the damaged goods policy...
   Sources:   ['damaged_goods.md']
--------------------------------------------------------------------------------
...
========================================
EVALUATION SUMMARY REPORT
========================================
10 test cases
Correct: 10
Incorrect: 0
Accuracy: 100%
========================================
```

---

## 🌐 API Endpoints Reference

| Method | Endpoint | Description | Protected |
| :--- | :--- | :--- | :--- |
| `POST` | `/register` | Register a new user (`email`, `password`) | No |
| `POST` | `/login` | Authenticate user and issue JWT | No |
| `GET` | `/me` | Get currently logged-in user profile | **Yes (Bearer)** |
| `POST` | `/tickets` | Submit customer ticket and generate AI decision | **Yes (Bearer)** |
| `GET` | `/tickets` | List authenticated user's tickets & decisions | **Yes (Bearer)** |
| `GET` | `/tickets/{id}`| Retrieve a specific ticket (strictly isolated) | **Yes (Bearer)** |

---

## 🔒 Security Best Practices Implemented
- Passwords hashed using industry-standard bcrypt algorithm.
- Multi-tenant data segregation: Each ticket query validates `ticket.user_id == current_user.id`.
- Foreign keys enforced in SQLite via `PRAGMA foreign_keys = ON;`.
- Secrets stored via environment variables (`.env`), not committed to git.
