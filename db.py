"""SQLite-Persistenz für User, Company und Analysen."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

import bcrypt

DB_PATH = Path(__file__).parent / "data" / "esg.db"


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


COMPANY_EXTRA_COLUMNS = [
    ("balance_sheet_eur", "REAL DEFAULT 0"),
    ("legal_form", "TEXT"),
    ("group_role", "TEXT"),
    ("env_claims", "INTEGER DEFAULT 0"),
    ("product_categories_json", "TEXT"),
    ("employees_de", "INTEGER DEFAULT 0"),
    ("language", "TEXT DEFAULT 'de'"),
    ("eu_importer", "INTEGER DEFAULT 0"),
]


def _migrate_companies(c: sqlite3.Connection) -> None:
    cols = {row[1] for row in c.execute("PRAGMA table_info(companies)").fetchall()}
    for col, ddl in COMPANY_EXTRA_COLUMNS:
        if col not in cols:
            c.execute(f"ALTER TABLE companies ADD COLUMN {col} {ddl}")


def init_db() -> None:
    with _conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                pw_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                name TEXT,
                employees INTEGER,
                revenue_eur REAL,
                branch TEXT,
                b2c INTEGER DEFAULT 0,
                listed INTEGER DEFAULT 0,
                sites_json TEXT,
                updated_at TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                result_json TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS analysis_cache (
                user_id INTEGER NOT NULL,
                profile_hash TEXT NOT NULL,
                reg_key TEXT NOT NULL,
                reg_hash TEXT NOT NULL,
                result_json TEXT NOT NULL,
                cached_at TEXT NOT NULL,
                PRIMARY KEY (user_id, profile_hash, reg_key),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            """
        )
        _migrate_companies(c)


# ---------- Users ----------
def create_user(email: str, password: str) -> int:
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO users (email, pw_hash, created_at) VALUES (?, ?, ?)",
            (email.lower().strip(), pw_hash, datetime.utcnow().isoformat()),
        )
        return cur.lastrowid


def verify_user(email: str, password: str) -> Optional[int]:
    with _conn() as c:
        row = c.execute(
            "SELECT id, pw_hash FROM users WHERE email = ?", (email.lower().strip(),)
        ).fetchone()
    if not row:
        return None
    if bcrypt.checkpw(password.encode(), row["pw_hash"].encode()):
        return row["id"]
    return None


def email_exists(email: str) -> bool:
    with _conn() as c:
        return c.execute("SELECT 1 FROM users WHERE email = ?", (email.lower().strip(),)).fetchone() is not None


# ---------- Company ----------
def get_company(user_id: int) -> Optional[dict]:
    with _conn() as c:
        row = c.execute("SELECT * FROM companies WHERE user_id = ?", (user_id,)).fetchone()
    if not row:
        return None
    data = dict(row)
    data["sites"] = json.loads(data.pop("sites_json") or "[]")
    data["product_categories"] = json.loads(data.pop("product_categories_json") or "[]")
    data["b2c"] = bool(data.get("b2c"))
    data["listed"] = bool(data.get("listed"))
    data["env_claims"] = bool(data.get("env_claims"))
    data["eu_importer"] = bool(data.get("eu_importer"))
    return data


def upsert_company(user_id: int, data: dict) -> None:
    sites_json = json.dumps(data.get("sites", []), ensure_ascii=False)
    products_json = json.dumps(data.get("product_categories", []), ensure_ascii=False)
    now = datetime.utcnow().isoformat()
    with _conn() as c:
        c.execute(
            """
            INSERT INTO companies (
                user_id, name, employees, revenue_eur, branch, b2c, listed,
                sites_json, updated_at, balance_sheet_eur, legal_form, group_role,
                env_claims, product_categories_json, employees_de, language,
                eu_importer
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name=excluded.name,
                employees=excluded.employees,
                revenue_eur=excluded.revenue_eur,
                branch=excluded.branch,
                b2c=excluded.b2c,
                listed=excluded.listed,
                sites_json=excluded.sites_json,
                updated_at=excluded.updated_at,
                balance_sheet_eur=excluded.balance_sheet_eur,
                legal_form=excluded.legal_form,
                group_role=excluded.group_role,
                env_claims=excluded.env_claims,
                product_categories_json=excluded.product_categories_json,
                employees_de=excluded.employees_de,
                language=excluded.language,
                eu_importer=excluded.eu_importer
            """,
            (
                user_id,
                data.get("name"),
                int(data.get("employees") or 0),
                float(data.get("revenue_eur") or 0),
                data.get("branch"),
                1 if data.get("b2c") else 0,
                1 if data.get("listed") else 0,
                sites_json,
                now,
                float(data.get("balance_sheet_eur") or 0),
                data.get("legal_form"),
                data.get("group_role"),
                1 if data.get("env_claims") else 0,
                products_json,
                int(data.get("employees_de") or 0),
                data.get("language") or "de",
                1 if data.get("eu_importer") else 0,
            ),
        )


# ---------- Analyses ----------
def save_analysis(user_id: int, result: list[dict]) -> int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO analyses (user_id, created_at, result_json) VALUES (?, ?, ?)",
            (user_id, datetime.utcnow().isoformat(), json.dumps(result, ensure_ascii=False)),
        )
        return cur.lastrowid


# ---------- Cache ----------
def get_cache(user_id: int, profile_hash: str) -> dict[str, dict]:
    with _conn() as c:
        rows = c.execute(
            "SELECT reg_key, reg_hash, result_json, cached_at FROM analysis_cache "
            "WHERE user_id = ? AND profile_hash = ?",
            (user_id, profile_hash),
        ).fetchall()
    return {
        row["reg_key"]: {
            "reg_hash": row["reg_hash"],
            "cached_at": row["cached_at"],
            "result": json.loads(row["result_json"]),
        }
        for row in rows
    }


def put_cache(user_id: int, profile_hash: str, reg_key: str, reg_hash: str, result: dict) -> None:
    with _conn() as c:
        c.execute(
            """
            INSERT INTO analysis_cache (user_id, profile_hash, reg_key, reg_hash, result_json, cached_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, profile_hash, reg_key) DO UPDATE SET
                reg_hash=excluded.reg_hash,
                result_json=excluded.result_json,
                cached_at=excluded.cached_at
            """,
            (user_id, profile_hash, reg_key, reg_hash, json.dumps(result, ensure_ascii=False),
             datetime.utcnow().isoformat()),
        )


def latest_analysis(user_id: int) -> Optional[dict]:
    with _conn() as c:
        row = c.execute(
            "SELECT id, created_at, result_json FROM analyses WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    if not row:
        return None
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "result": json.loads(row["result_json"]),
    }
