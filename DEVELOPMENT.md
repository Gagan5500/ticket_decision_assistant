# Development Log & AI Agentic Workflow Report

This document records the architectural decisions, design tradeoffs, security models, and AI agentic development workflow employed while building the **Minimal AI Support Decision API**.

---

## 1. AI Coding Agent Workflow

During the development of this project, we leveraged modern AI agentic pair-programming (Antigravity):
- **Planning & Specification Breakdown**: Translated the shortlist assignment requirements into an actionable specification covering database schemas, REST API endpoints, JWT authentication, RAG pipelines, and Streamlit frontends.
- **Test-Driven Security**: Generated explicit test cases early, specifically validating authorization boundaries (preventing IDOR vulnerabilities such as Alice attempting to view Bob's tickets).
- **Graceful Fallbacks & Offline Resilience**: Implemented a dual-mode decision engine: utilizing Gemini 2.5 Flash when an API key is present, backed by a deterministic, TF-IDF grounded fallback so the system remains fully testable offline without third-party API dependencies.

---

## 2. Key Architectural Decisions & Tradeoffs

### A. RAG vs. CAG (Context Augmented Generation)
- **Tradeoff**: The prompt guidelines suggested considering CAG (loading all policies into the prompt context) vs. RAG (chunking and retrieving).
- **Decision**: We implemented both capabilities within `src/retrieval.py`:
  1. **Local RAG Retrieval (Primary)**: Chunks policies by header sections (`##`), extracts keywords, and computes TF-IDF cosine similarity via NumPy. This keeps the LLM context lean, focused, and token-efficient.
  2. **CAG Capability (`get_all_policy_context`)**: Available for scenarios where policies are concise (<10k tokens) and zero-retrieval latency is desired.
- **Why Local NumPy over Pinecone/Chroma**: Avoiding external vector DBs simplifies installation, eliminates cloud costs, and ensures zero external infrastructure dependencies for an intern assignment.

### B. Multi-Tenant Authorization (IDOR Prevention)
- **Problem**: Authentication (verifying who the user is) is insufficient on its own. Insecure Direct Object References (IDOR) occur if user A can query `/tickets/{id}` belonging to user B.
- **Implementation**:
  - The JWT payload encodes the user's ID as the `sub` claim.
  - The `get_ticket(ticket_id)` endpoint queries the ticket and asserts `ticket["user_id"] == current_user["id"]`.
  - If a mismatch occurs, the API returns a strict `403 FORBIDDEN`.
  - Validated by `tests/test_isolation.py`.

### C. Frontend Architecture: Strict HTTP Decoupling
- **Requirement**: Streamlit must communicate with the FastAPI backend through HTTP requests rather than directly querying SQLite.
- **Implementation**:
  - `streamlit_app.py` acts as a pure API client.
  - It maintains the JWT access token in `st.session_state.auth_token` and attaches the `Authorization: Bearer <token>` header to all data requests.
  - This ensures that business logic, authorization rules, and AI decision logic remain centralized in the FastAPI backend.

### D. SQLite Integrity & Concurrency
- SQLite by default does not enforce foreign keys unless explicitly instructed.
- We configured `PRAGMA foreign_keys = ON;` on every database connection to ensure cascading deletes and foreign key constraints between `users -> tickets -> decisions`.
- Used `check_same_thread=False` with isolated transactions to support concurrent HTTP requests.

---

## 3. Grounding & Hallucination Mitigation

A key requirement in Section 8 is:
> *"The system must not invent an answer when the available information is insufficient. In such cases it should return a clear value such as NEEDS_MORE_INFORMATION."*

To achieve this:
1. **Prompt Constraints**: The system prompt explicitly commands the model not to invent order values, dates, or product conditions.
2. **Schema Enforcement**: Outputs are validated via Pydantic (`DecisionResult`), ensuring `action`, `confidence`, `reason`, and `sources` are strictly typed.
3. **Threshold Logic**: Specific numerical rules (e.g., the ₹2,000 photo threshold for damaged goods, 7-day return window) are explicitly checked against evidence extracted from the ticket.
4. **Vagueness Guard**: When tickets are missing essential identifiers (e.g. *"Help, my item is broken!"*), the decision engine immediately triggers `action: "NEEDS_MORE_INFORMATION"`.

---

## 4. Evaluation Benchmark Results

The evaluation runner (`src/evaluate.py`) tests the system against 10 diverse scenarios covering:
- Damaged goods above ₹2,000 threshold (`REQUEST_PHOTOS`)
- Damaged goods under ₹2,000 (`APPROVE_REPLACEMENT`)
- Expired return window (`REJECT_RETURN`)
- Valid return within 7 days (`APPROVE_RETURN`)
- Lost shipment after 10 business days (`APPROVE_LOST_TRANSIT_CLAIM`)
- In-transit address rerouting (`REJECT_REROUTE`)
- Delayed refund escalation (`ESCALATE_TO_BILLING`)
- Pre-dispatch cancellation (`APPROVE_REFUND`)
- Clearance/final-sale exclusion (`REJECT_RETURN`)
- Ambiguous/incomplete query (`NEEDS_MORE_INFORMATION`)

**Result**: 100% accuracy on standard benchmark test cases with clear grounding citations.
