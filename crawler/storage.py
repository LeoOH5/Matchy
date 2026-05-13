"""
SQLite 기반 정책 데이터 저장소
"""
import json
import sqlite3
from pathlib import Path
from datetime import datetime

from crawler.models import Policy


DB_PATH = Path(__file__).parent.parent / "data" / "policies.db"


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS policies (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            source TEXT NOT NULL,
            source_url TEXT,
            policy_type TEXT NOT NULL,
            description TEXT,
            age_min INTEGER,
            age_max INTEGER,
            income_max INTEGER,
            income_ratio REAL,
            income_desc TEXT,
            regions TEXT,          -- JSON array
            loan_rate_min REAL,
            loan_rate_max REAL,
            loan_amount_max INTEGER,
            loan_period_max INTEGER,
            loan_collateral TEXT,
            grant_amount INTEGER,
            application_url TEXT,
            application_period TEXT,
            tags TEXT,             -- JSON array
            crawled_at TEXT,
            is_active INTEGER DEFAULT 1
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_policy_type ON policies(policy_type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_source ON policies(source)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_is_active ON policies(is_active)")
    conn.commit()
    conn.close()


def upsert_policy(policy: Policy):
    conn = get_connection()
    policy_id = policy.id or f"{policy.source}_{policy.name}"

    conn.execute("""
        INSERT OR REPLACE INTO policies (
            id, name, source, source_url, policy_type, description,
            age_min, age_max,
            income_max, income_ratio, income_desc,
            regions,
            loan_rate_min, loan_rate_max, loan_amount_max, loan_period_max, loan_collateral,
            grant_amount, application_url, application_period,
            tags, crawled_at, is_active
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        policy_id,
        policy.name,
        policy.source,
        policy.source_url,
        policy.policy_type.value,
        policy.description,
        policy.age.min_age if policy.age else None,
        policy.age.max_age if policy.age else None,
        policy.income.max_income if policy.income else None,
        policy.income.max_income_ratio if policy.income else None,
        policy.income.description if policy.income else None,
        json.dumps(policy.regions, ensure_ascii=False),
        policy.loan.min_rate if policy.loan else None,
        policy.loan.max_rate if policy.loan else None,
        policy.loan.max_amount if policy.loan else None,
        policy.loan.max_period if policy.loan else None,
        policy.loan.collateral if policy.loan else None,
        policy.grant_amount,
        policy.application_url,
        policy.application_period,
        json.dumps(policy.tags, ensure_ascii=False),
        policy.crawled_at.isoformat(),
        1 if policy.is_active else 0,
    ))
    conn.commit()
    conn.close()


def bulk_upsert(policies: list[Policy]):
    for p in policies:
        upsert_policy(p)


def search_policies(
    query: str = "",
    policy_type: str | None = None,
    age: int | None = None,
    income: int | None = None,
    region: str | None = None,
    max_rate: float | None = None,
    max_amount: int | None = None,
) -> list[dict]:
    conn = get_connection()
    conditions = ["is_active = 1"]
    params: list = []

    if policy_type:
        conditions.append("policy_type = ?")
        params.append(policy_type)

    if age is not None:
        conditions.append("(age_min IS NULL OR age_min <= ?) AND (age_max IS NULL OR age_max >= ?)")
        params.extend([age, age])

    if income is not None:
        conditions.append("(income_max IS NULL OR income_max >= ?)")
        params.append(income)

    if region:
        conditions.append("(regions = '[]' OR regions LIKE ?)")
        params.append(f'%"{region}"%')

    if max_rate is not None:
        conditions.append("(loan_rate_min IS NULL OR loan_rate_min <= ?)")
        params.append(max_rate)

    if max_amount is not None:
        conditions.append("(loan_amount_max IS NULL OR loan_amount_max >= ?)")
        params.append(max_amount)

    if query:
        conditions.append("(name LIKE ? OR description LIKE ? OR tags LIKE ?)")
        q = f"%{query}%"
        params.extend([q, q, q])

    where = " AND ".join(conditions)
    sql = f"SELECT * FROM policies WHERE {where} ORDER BY loan_rate_min ASC NULLS LAST"

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    results = []
    for row in rows:
        d = dict(row)
        d["regions"] = json.loads(d["regions"] or "[]")
        d["tags"] = json.loads(d["tags"] or "[]")
        results.append(d)
    return results


def get_stats() -> dict:
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM policies WHERE is_active=1").fetchone()[0]
    by_type = conn.execute(
        "SELECT policy_type, COUNT(*) as cnt FROM policies WHERE is_active=1 GROUP BY policy_type"
    ).fetchall()
    by_source = conn.execute(
        "SELECT source, COUNT(*) as cnt FROM policies WHERE is_active=1 GROUP BY source"
    ).fetchall()
    conn.close()
    return {
        "total": total,
        "by_type": {row["policy_type"]: row["cnt"] for row in by_type},
        "by_source": {row["source"]: row["cnt"] for row in by_source},
    }
