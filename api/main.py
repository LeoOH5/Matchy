"""
청년 정책 매칭 API
"""
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crawler.storage import init_db, search_policies, get_stats

app = FastAPI(title="청년 정책 매칭 API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001", "http://localhost:3002"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class UserProfile(BaseModel):
    name: str
    birth_year: int
    gender: str                           # "male" | "female"
    income: int                           # 연소득 (만원)
    region: str                           # 거주 지역
    employment_status: str                # "employed" | "unemployed" | "student" | "freelance"
    employment_type: Optional[str] = None # "sme" | "large" | "public" | None
    housing_type: str                     # "jeonse" | "monthly" | "own" | "parents"
    marital_status: str                   # "single" | "married" | "newlywed"
    purpose: list[str]                    # ["전세대출", "월세대출", "창업지원", "취업지원", ...]
    household_members: int = 1
    assets: Optional[int] = None          # 자산 (만원), 선택


@app.on_event("startup")
def startup():
    init_db()


@app.post("/api/match")
def match_policies(profile: UserProfile):
    current_year = 2026
    age = current_year - profile.birth_year + 1  # 한국식 나이

    all_results = []

    for purpose in profile.purpose:
        keyword_map = {
            "전세대출": "전세",
            "월세대출": "월세",
            "창업지원": "창업",
            "취업지원": "취업",
            "교육비": "교육",
            "주거지원": "주거",
            "원룸대출": "전세",
        }
        query = keyword_map.get(purpose, purpose)

        results = search_policies(
            query=query,
            age=age,
            income=profile.income,
            region=profile.region if profile.region != "전국" else None,
        )
        all_results.extend(results)

    # 중복 제거
    seen = set()
    unique = []
    for r in all_results:
        if r["id"] not in seen:
            seen.add(r["id"])
            unique.append(r)

    # 중소기업 재직자 여부로 추가 상품 포함
    if profile.employment_type == "sme":
        sme_results = search_policies(query="중소기업", age=age, income=profile.income)
        for r in sme_results:
            if r["id"] not in seen:
                seen.add(r["id"])
                unique.append(r)

    # 신혼부부 상품 포함
    if profile.marital_status == "newlywed":
        newlywed_results = search_policies(query="신혼", age=age)
        for r in newlywed_results:
            if r["id"] not in seen:
                seen.add(r["id"])
                unique.append(r)

    # 정렬: 금리 낮은 순 → 한도 높은 순
    unique.sort(key=lambda x: (
        x.get("loan_rate_min") or 99,
        -(x.get("loan_amount_max") or 0),
    ))

    return {
        "age": age,
        "matched_count": len(unique),
        "policies": unique,
    }


@app.get("/api/policies")
def get_policies(
    query: str = Query(default=""),
    policy_type: Optional[str] = None,
    age: Optional[int] = None,
    income: Optional[int] = None,
    region: Optional[str] = None,
):
    results = search_policies(
        query=query,
        policy_type=policy_type,
        age=age,
        income=income,
        region=region,
    )
    return {"count": len(results), "policies": results}


@app.get("/api/stats")
def stats():
    return get_stats()
