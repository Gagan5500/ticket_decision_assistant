import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

def get_db_path(custom_path: Optional[str] = None) -> str:
    if custom_path:
        return custom_path
    return os.getenv("DATABASE_PATH", "app.db")

def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = get_db_path(db_path)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db(db_path: Optional[str] = None) -> None:
    """Initialize the SQLite database with required tables."""
    path = get_db_path(db_path)
    conn = get_db_connection(path)
    cursor = conn.cursor()
    
    # 1. users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. tickets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );
    """)

    # 3. decisions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_id INTEGER NOT NULL UNIQUE,
            action TEXT NOT NULL,
            reason TEXT NOT NULL,
            confidence REAL NOT NULL,
            sources TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()

def _ensure_db_initialized(db_path: Optional[str] = None) -> None:
    path = get_db_path(db_path)
    conn = get_db_connection(path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    if not cursor.fetchone():
        conn.close()
        init_db(path)
    else:
        conn.close()

# User CRUD
def create_user(email: str, password_hash: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    _ensure_db_initialized(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (email, password_hash) VALUES (?, ?)",
            (email.strip().lower(), password_hash)
        )
        conn.commit()
        user_id = cursor.lastrowid
        cursor.execute("SELECT id, email, created_at FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row)
    finally:
        conn.close()

def get_user_by_email(email: str, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    _ensure_db_initialized(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

def get_user_by_id(user_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    _ensure_db_initialized(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, email, created_at FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    finally:
        conn.close()

# Ticket & Decision CRUD
def create_ticket(user_id: int, message: str, db_path: Optional[str] = None) -> Dict[str, Any]:
    _ensure_db_initialized(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO tickets (user_id, message) VALUES (?, ?)",
            (user_id, message.strip())
        )
        conn.commit()
        ticket_id = cursor.lastrowid
        cursor.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,))
        row = cursor.fetchone()
        return dict(row)
    finally:
        conn.close()

def create_decision(
    ticket_id: int,
    action: str,
    reason: str,
    confidence: float,
    sources: List[str],
    db_path: Optional[str] = None
) -> Dict[str, Any]:
    _ensure_db_initialized(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        sources_json = json.dumps(sources)
        cursor.execute(
            """
            INSERT INTO decisions (ticket_id, action, reason, confidence, sources)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ticket_id, action, reason, float(confidence), sources_json)
        )
        conn.commit()
        decision_id = cursor.lastrowid
        cursor.execute("SELECT * FROM decisions WHERE id = ?", (decision_id,))
        row = cursor.fetchone()
        res = dict(row)
        res["sources"] = json.loads(res["sources"])
        return res
    finally:
        conn.close()

def get_tickets_for_user(user_id: int, db_path: Optional[str] = None) -> List[Dict[str, Any]]:
    _ensure_db_initialized(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT 
                t.id as ticket_id,
                t.user_id,
                t.message,
                t.created_at as ticket_created_at,
                d.id as decision_id,
                d.action,
                d.reason,
                d.confidence,
                d.sources,
                d.created_at as decision_created_at
            FROM tickets t
            LEFT JOIN decisions d ON t.id = d.ticket_id
            WHERE t.user_id = ?
            ORDER BY t.created_at DESC
            """,
            (user_id,)
        )
        rows = cursor.fetchall()
        results = []
        for r in rows:
            item = dict(r)
            if item.get("sources"):
                try:
                    item["sources"] = json.loads(item["sources"])
                except Exception:
                    item["sources"] = []
            else:
                item["sources"] = []
            results.append(item)
        return results
    finally:
        conn.close()

def get_ticket_with_decision(ticket_id: int, db_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    _ensure_db_initialized(db_path)
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT 
                t.id as ticket_id,
                t.user_id,
                t.message,
                t.created_at as ticket_created_at,
                d.id as decision_id,
                d.action,
                d.reason,
                d.confidence,
                d.sources,
                d.created_at as decision_created_at
            FROM tickets t
            LEFT JOIN decisions d ON t.id = d.ticket_id
            WHERE t.id = ?
            """,
            (ticket_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        res = dict(row)
        if res.get("sources"):
            try:
                res["sources"] = json.loads(res["sources"])
            except Exception:
                res["sources"] = []
        else:
            res["sources"] = []
        return res
    finally:
        conn.close()
