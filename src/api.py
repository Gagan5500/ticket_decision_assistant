import os
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, status, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

from src.database import (
    init_db,
    create_user,
    get_user_by_email,
    get_user_by_id,
    create_ticket,
    create_decision,
    get_tickets_for_user,
    get_ticket_with_decision
)
from src.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)
from src.decision import evaluate_ticket, DecisionResult

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database on startup
    init_db()
    yield

app = FastAPI(
    title="Minimal AI Decision API",
    description="Support-ticket decision assistant API powered by FastAPI, SQLite, JWT, and RAG",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for local development / Streamlit integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Request / Response Models -----------------

class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, description="Password must be at least 6 characters")

class UserLoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str

class UserProfileResponse(BaseModel):
    id: int
    email: str
    created_at: Optional[str] = None

class TicketCreateRequest(BaseModel):
    message: str = Field(min_length=3, description="Customer ticket message")

class DecisionResponseModel(BaseModel):
    id: Optional[int] = None
    action: str
    reason: str
    confidence: float
    sources: List[str]
    created_at: Optional[str] = None

class TicketDetailResponse(BaseModel):
    ticket_id: int
    user_id: int
    message: str
    ticket_created_at: Optional[str] = None
    decision: Optional[DecisionResponseModel] = None

# ----------------- Endpoints -----------------

@app.get("/")
def root():
    return {
        "status": "online",
        "service": "AI Decision API",
        "docs_url": "/docs"
    }

@app.post("/register", response_model=UserProfileResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegisterRequest):
    existing = get_user_by_email(user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    pw_hash = hash_password(user_data.password)
    new_user = create_user(user_data.email, pw_hash)
    return {
        "id": new_user["id"],
        "email": new_user["email"],
        "created_at": str(new_user.get("created_at", ""))
    }

@app.post("/login", response_model=TokenResponse)
def login(login_data: UserLoginRequest):
    user = get_user_by_email(login_data.email)
    if not user or not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(data={"sub": str(user["id"]), "email": user["email"]})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user["id"],
        "email": user["email"]
    }

@app.get("/me", response_model=UserProfileResponse)
def get_me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "created_at": str(current_user.get("created_at", ""))
    }

@app.post("/tickets", response_model=TicketDetailResponse, status_code=status.HTTP_201_CREATED)
def submit_ticket(
    ticket_data: TicketCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    # 1. Create ticket entry
    ticket = create_ticket(user_id=current_user["id"], message=ticket_data.message)
    ticket_id = ticket["id"]

    # 2. Run RAG retrieval & AI Decision
    decision_result = evaluate_ticket(ticket_data.message)

    # 3. Store decision in database
    decision_record = create_decision(
        ticket_id=ticket_id,
        action=decision_result.action,
        reason=decision_result.reason,
        confidence=decision_result.confidence,
        sources=decision_result.sources
    )

    return {
        "ticket_id": ticket_id,
        "user_id": current_user["id"],
        "message": ticket["message"],
        "ticket_created_at": str(ticket.get("created_at", "")),
        "decision": {
            "id": decision_record["id"],
            "action": decision_record["action"],
            "reason": decision_record["reason"],
            "confidence": decision_record["confidence"],
            "sources": decision_record["sources"],
            "created_at": str(decision_record.get("created_at", ""))
        }
    }

@app.get("/tickets", response_model=List[TicketDetailResponse])
def list_tickets(current_user: dict = Depends(get_current_user)):
    user_tickets = get_tickets_for_user(current_user["id"])
    response = []
    for t in user_tickets:
        dec = None
        if t.get("decision_id"):
            dec = {
                "id": t["decision_id"],
                "action": t["action"],
                "reason": t["reason"],
                "confidence": t["confidence"],
                "sources": t["sources"],
                "created_at": str(t.get("decision_created_at", ""))
            }
        response.append({
            "ticket_id": t["ticket_id"],
            "user_id": t["user_id"],
            "message": t["message"],
            "ticket_created_at": str(t.get("ticket_created_at", "")),
            "decision": dec
        })
    return response

@app.get("/tickets/{ticket_id}", response_model=TicketDetailResponse)
def get_ticket(
    ticket_id: int,
    current_user: dict = Depends(get_current_user)
):
    ticket_record = get_ticket_with_decision(ticket_id)
    if not ticket_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket #{ticket_id} not found"
        )
    
    # Strict multi-tenant authorization check
    if ticket_record["user_id"] != current_user["id"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You do not have permission to access this ticket."
        )

    dec = None
    if ticket_record.get("decision_id"):
        dec = {
            "id": ticket_record["decision_id"],
            "action": ticket_record["action"],
            "reason": ticket_record["reason"],
            "confidence": ticket_record["confidence"],
            "sources": ticket_record["sources"],
            "created_at": str(ticket_record.get("decision_created_at", ""))
        }

    return {
        "ticket_id": ticket_record["ticket_id"],
        "user_id": ticket_record["user_id"],
        "message": ticket_record["message"],
        "ticket_created_at": str(ticket_record.get("ticket_created_at", "")),
        "decision": dec
    }
