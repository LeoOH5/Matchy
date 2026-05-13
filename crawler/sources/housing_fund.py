"""
주택도시기금 (nhuf.molit.go.kr) 크롤러
- 청년전용 버팀목전세자금대출
- 중소기업취업청년 전월세보증금대출
- 청년전용 보증부월세대출
- 신혼부부전용 전세자금

정부 사이트 구조 변경이 잦아 static 기준값을 유지하고,
라이브 크롤링 성공 시 금리만 업데이트하는 방식으로 동작.
"""
import re
import time
import requests
from bs4 import BeautifulSoup

from crawler.models import Policy, PolicyType, AgeRange, IncomeCondition, LoanDetails


BASE_URL = "https://nhuf.molit.go.kr"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# 기준 상품 데이터 (2025년 기준 공식 조건)
LOAN_PRODUCTS = [
    {
        "id": "youth_jeonse",
        "name": "청년전용 버팀목전세자금",
        "url": "https://nhuf.molit.go.kr/FP/NH05/NH0503/NH050301/selectNH0503010000.jsp",
        "description": "만 19~34세 무주택 세대주 대상 전세자금 대출. 연소득 5천만원 이하.",
        "tags": ["전세", "주거", "청년", "대출", "버팀목"],
        "age": AgeRange(min_age=19, max_age=34),
        "income": IncomeCondition(max_income=5000, description="연소득 5천만원 이하"),
        "loan": LoanDetails(
            min_rate=1.8, max_rate=2.7,
            max_amount=10000,   # 1억원
            max_period=120,     # 10년 (2년 단위 갱신)
            collateral="한국주택금융공사 보증",
        ),
    },
    {
        "id": "sme_youth_jeonse",
        "name": "중소기업취업청년 전월세보증금대출",
        "url": "https://nhuf.molit.go.kr/FP/NH05/NH0503/NH050302/selectNH0503020000.jsp",
        "description": "중소·중견기업 재직 만 19~34세 청년 대상. 연소득 3500만원 이하.",
        "tags": ["전세", "월세", "청년", "대출", "중소기업"],
        "age": AgeRange(min_age=19, max_age=34),
        "income": IncomeCondition(max_income=3500, description="연소득 3500만원 이하"),
        "loan": LoanDetails(
            min_rate=1.2, max_rate=1.2,  # 고정 연 1.2%
            max_amount=10000,
            max_period=120,
            collateral="한국주택금융공사 보증",
        ),
    },
    {
        "id": "youth_monthly_rent",
        "name": "청년전용 보증부월세대출",
        "url": "https://nhuf.molit.go.kr/FP/NH05/NH0503/NH050303/selectNH0503030000.jsp",
        "description": "만 19~34세 무주택 단독세대주 대상 월세보증금+월세 대출. 연소득 2천만원 이하.",
        "tags": ["월세", "주거", "청년", "대출"],
        "age": AgeRange(min_age=19, max_age=34),
        "income": IncomeCondition(max_income=2000, description="연소득 2천만원 이하"),
        "loan": LoanDetails(
            min_rate=1.3, max_rate=2.1,
            max_amount=3000,    # 보증금 3000만원 + 월세 960만원
            max_period=24,
            collateral="한국주택금융공사 보증",
        ),
    },
    {
        "id": "newlywed_jeonse",
        "name": "신혼부부전용 전세자금",
        "url": "https://nhuf.molit.go.kr/FP/NH05/NH0503/NH050304/selectNH0503040000.jsp",
        "description": "혼인 7년 이내 무주택 세대주 대상. 합산 연소득 6천만원 이하.",
        "tags": ["전세", "신혼", "대출", "주거"],
        "age": AgeRange(min_age=19, max_age=45),
        "income": IncomeCondition(max_income=6000, description="부부합산 연소득 6천만원 이하"),
        "loan": LoanDetails(
            min_rate=1.5, max_rate=2.4,
            max_amount=30000,   # 3억원
            max_period=120,
            collateral="한국주택금융공사 보증",
        ),
    },
]


def _try_fetch_rate(session: requests.Session, url: str) -> tuple[float | None, float | None]:
    """라이브 크롤링으로 현재 금리 가져오기 (실패해도 무방)"""
    try:
        resp = session.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")
        text = soup.get_text()
        rates = [float(r) for r in re.findall(r"(\d+\.\d+)\s*%", text)
                 if 0.5 <= float(r) <= 15.0]
        if len(rates) >= 2:
            return min(rates), max(rates)
        elif len(rates) == 1:
            return rates[0], rates[0]
    except Exception:
        pass
    return None, None


def crawl_housing_fund() -> list[Policy]:
    session = requests.Session()
    policies = []

    for product in LOAN_PRODUCTS:
        loan = product["loan"]

        # 라이브 금리 업데이트 시도
        live_min, live_max = _try_fetch_rate(session, product["url"])
        if live_min is not None:
            loan = LoanDetails(
                min_rate=live_min,
                max_rate=live_max,
                max_amount=loan.max_amount,
                max_period=loan.max_period,
                collateral=loan.collateral,
            )

        policy = Policy(
            id=product["id"],
            name=product["name"],
            source="주택도시기금",
            source_url=product["url"],
            policy_type=PolicyType.LOAN_HOUSING,
            description=product["description"],
            age=product["age"],
            income=product["income"],
            loan=loan,
            application_url=product["url"],
            tags=product["tags"],
        )
        policies.append(policy)
        print(f"[housing_fund] 수집 완료: {product['name']} (금리 {'라이브' if live_min else '기준값'})")
        time.sleep(0.5)

    return policies
