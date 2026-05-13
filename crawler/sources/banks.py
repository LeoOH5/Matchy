"""
시중은행 청년 대출 상품 크롤러
- KB국민은행
- 신한은행
- 우리은행
- 하나은행
- IBK기업은행
"""
import re
import time
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

from crawler.models import Policy, PolicyType, AgeRange, LoanDetails


HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
}

# 시중은행 청년 대출 상품 정의
BANK_PRODUCTS = [
    # KB국민은행
    {
        "id": "kb_youth_jeonse",
        "name": "KB 청년전세대출",
        "bank": "KB국민은행",
        "url": "https://obank.kbstar.com/quics?page=C101351",
        "policy_type": PolicyType.LOAN_HOUSING,
        "tags": ["전세", "청년", "KB국민은행", "대출"],
        "static_data": {
            "age": AgeRange(min_age=19, max_age=34),
            "loan": LoanDetails(
                min_rate=2.0, max_rate=4.5,
                max_amount=20000,  # 2억원
                max_period=120,    # 10년
            ),
        },
    },
    # 신한은행
    {
        "id": "shinhan_youth_jeonse",
        "name": "신한 청년대출",
        "bank": "신한은행",
        "url": "https://www.shinhan.com/hpe/index.jsp#050101010000",
        "policy_type": PolicyType.LOAN_HOUSING,
        "tags": ["청년", "신한은행", "대출", "주거"],
        "static_data": {
            "age": AgeRange(min_age=19, max_age=34),
            "loan": LoanDetails(
                min_rate=3.0, max_rate=5.0,
                max_amount=25000,
                max_period=120,
            ),
        },
    },
    # 우리은행
    {
        "id": "woori_youth",
        "name": "우리 청년 전월세대출",
        "bank": "우리은행",
        "url": "https://spot.wooribank.com/pot/Dream?withyou=POLON0029",
        "policy_type": PolicyType.LOAN_HOUSING,
        "tags": ["전세", "월세", "청년", "우리은행", "대출"],
        "static_data": {
            "age": AgeRange(min_age=19, max_age=34),
            "loan": LoanDetails(
                min_rate=2.8, max_rate=4.8,
                max_amount=15000,
                max_period=120,
            ),
        },
    },
    # IBK기업은행
    {
        "id": "ibk_youth_jeonse",
        "name": "IBK 청년전세대출",
        "bank": "IBK기업은행",
        "url": "https://www.ibk.co.kr/renew/main.ibk",
        "policy_type": PolicyType.LOAN_HOUSING,
        "tags": ["전세", "청년", "IBK기업은행", "대출"],
        "static_data": {
            "age": AgeRange(min_age=19, max_age=34),
            "loan": LoanDetails(
                min_rate=2.5, max_rate=4.2,
                max_amount=20000,
                max_period=120,
            ),
        },
    },
    # 카카오뱅크
    {
        "id": "kakao_youth_jeonse",
        "name": "카카오뱅크 청년 전월세보증금 대출",
        "bank": "카카오뱅크",
        "url": "https://www.kakaobank.com/products/lease",
        "policy_type": PolicyType.LOAN_HOUSING,
        "tags": ["전세", "월세", "청년", "카카오뱅크", "대출", "인터넷은행"],
        "static_data": {
            "age": AgeRange(min_age=19, max_age=34),
            "loan": LoanDetails(
                min_rate=2.1, max_rate=3.8,
                max_amount=25000,
                max_period=120,
            ),
        },
    },
]


@retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=2, max=8))
def _try_fetch(session: requests.Session, url: str) -> BeautifulSoup | None:
    try:
        resp = session.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        return BeautifulSoup(resp.text, "lxml")
    except Exception:
        return None


def _extract_rate_from_page(soup: BeautifulSoup) -> tuple[float | None, float | None]:
    """페이지에서 금리 정보 추출 시도"""
    text = soup.get_text()
    rates = re.findall(r"(\d+\.\d+)\s*%", text)
    numeric_rates = [float(r) for r in rates if 0.5 <= float(r) <= 20.0]
    if len(numeric_rates) >= 2:
        return min(numeric_rates), max(numeric_rates)
    elif len(numeric_rates) == 1:
        return numeric_rates[0], numeric_rates[0]
    return None, None


def crawl_banks() -> list[Policy]:
    session = requests.Session()
    policies = []

    for product in BANK_PRODUCTS:
        try:
            # 실시간 크롤링 시도 (실패해도 static_data로 fallback)
            soup = _try_fetch(session, product["url"])
            loan_data = product["static_data"]["loan"]

            if soup:
                live_min, live_max = _extract_rate_from_page(soup)
                if live_min and live_max:
                    loan_data = LoanDetails(
                        min_rate=live_min,
                        max_rate=live_max,
                        max_amount=product["static_data"]["loan"].max_amount,
                        max_period=product["static_data"]["loan"].max_period,
                    )

            policy = Policy(
                id=product["id"],
                name=product["name"],
                source=product["bank"],
                source_url=product["url"],
                policy_type=product["policy_type"],
                age=product["static_data"]["age"],
                loan=loan_data,
                application_url=product["url"],
                tags=product["tags"],
            )
            policies.append(policy)
            print(f"[banks] 수집 완료: {product['name']}")
            time.sleep(0.8)

        except Exception as e:
            print(f"[banks] {product['name']} 오류: {e}")

    return policies
