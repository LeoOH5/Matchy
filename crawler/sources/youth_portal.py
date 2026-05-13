"""
청년정책포털 (youth.go.kr) 크롤러
- 중앙정부 및 지방정부 청년 정책 수집
"""
import re
import time
import requests
from bs4 import BeautifulSoup
from typing import Generator
from tenacity import retry, stop_after_attempt, wait_exponential

from crawler.models import Policy, PolicyType, AgeRange, IncomeCondition, LoanDetails


BASE_URL = "https://www.youthcenter.go.kr"
POLICY_LIST_URL = f"{BASE_URL}/youngPlcyUnif/youngPlcyUnifList.do"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": BASE_URL,
}

# 정책 유형 분류 매핑
TYPE_KEYWORDS = {
    PolicyType.LOAN_HOUSING: ["전월세", "주거", "원룸", "보증금", "주택", "임차", "매입"],
    PolicyType.LOAN_GOVT: ["대출", "융자", "금융"],
    PolicyType.GRANT: ["지원금", "장려금", "수당", "바우처", "보조"],
    PolicyType.EMPLOYMENT: ["취업", "일자리", "채용", "인턴"],
    PolicyType.EDUCATION: ["교육", "훈련", "학원", "자격증"],
}


def _classify_type(title: str, description: str) -> PolicyType:
    text = title + " " + description
    for ptype, keywords in TYPE_KEYWORDS.items():
        if any(kw in text for kw in keywords):
            return ptype
    return PolicyType.OTHER


def _extract_age(text: str) -> AgeRange | None:
    pattern = r"(\d{2})\s*~\s*(\d{2})\s*세"
    match = re.search(pattern, text)
    if match:
        return AgeRange(min_age=int(match.group(1)), max_age=int(match.group(2)))
    single = re.search(r"만\s*(\d{2})\s*세\s*이하", text)
    if single:
        return AgeRange(min_age=19, max_age=int(single.group(1)))
    return None


def _extract_regions(text: str) -> list[str]:
    regions = ["서울", "경기", "인천", "부산", "대구", "광주", "대전", "울산", "세종",
               "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주"]
    found = [r for r in regions if r in text]
    return found if found else []  # 빈 리스트 = 전국


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _get_page(session: requests.Session, page: int) -> dict:
    payload = {
        "pageIndex": page,
        "pageUnit": 10,
        "srchPolyBizSecd": "",   # 분야 전체
        "srchZoneCode": "",       # 지역 전체
    }
    resp = session.post(POLICY_LIST_URL, data=payload, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp


def _parse_detail(session: requests.Session, policy_id: str) -> dict:
    detail_url = f"{BASE_URL}/youngPlcyUnif/youngPlcyUnifDtl.do"
    resp = session.post(detail_url, data={"bizId": policy_id}, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    data = {}
    rows = soup.select("table.tbl_view tr")
    for row in rows:
        th = row.select_one("th")
        td = row.select_one("td")
        if th and td:
            data[th.get_text(strip=True)] = td.get_text(strip=True)

    return data


def crawl_youth_portal(max_pages: int = 50) -> Generator[Policy, None, None]:
    session = requests.Session()

    for page in range(1, max_pages + 1):
        try:
            resp = _get_page(session, page)
            soup = BeautifulSoup(resp.text, "lxml")

            items = soup.select("ul.policy_list > li") or soup.select(".list_policy li")
            if not items:
                # 마지막 페이지
                break

            for item in items:
                try:
                    title_el = item.select_one(".tit") or item.select_one("strong") or item.select_one("h3")
                    if not title_el:
                        continue

                    title = title_el.get_text(strip=True)
                    desc_el = item.select_one(".txt") or item.select_one("p")
                    description = desc_el.get_text(strip=True) if desc_el else ""

                    # 정책 ID 추출 (onclick 또는 href에서)
                    link = item.select_one("a[href]") or item.select_one("a[onclick]")
                    policy_id = None
                    if link:
                        onclick = link.get("onclick", "")
                        id_match = re.search(r"['\"]([A-Z0-9]{10,})['\"]", onclick)
                        if id_match:
                            policy_id = id_match.group(1)

                    source_url = f"{BASE_URL}/youngPlcyUnif/youngPlcyUnifDtl.do?bizId={policy_id}" if policy_id else None

                    # 지역 추출
                    region_el = item.select_one(".area") or item.select_one(".region")
                    region_text = region_el.get_text(strip=True) if region_el else ""

                    policy = Policy(
                        id=policy_id,
                        name=title,
                        source="청년정책포털",
                        source_url=source_url,
                        policy_type=_classify_type(title, description),
                        description=description,
                        age=_extract_age(description),
                        regions=_extract_regions(region_text),
                        tags=_auto_tags(title, description),
                    )
                    yield policy

                except Exception as e:
                    print(f"[youth_portal] 항목 파싱 오류: {e}")
                    continue

            time.sleep(0.5)

        except Exception as e:
            print(f"[youth_portal] 페이지 {page} 오류: {e}")
            break


def _auto_tags(title: str, desc: str) -> list[str]:
    tag_map = {
        "원룸": ["원룸", "주거"],
        "전세": ["전세", "주거"],
        "월세": ["월세", "주거"],
        "취업": ["취업"],
        "창업": ["창업"],
        "교육": ["교육"],
        "대출": ["대출"],
        "지원금": ["지원금"],
        "청년": ["청년"],
        "신혼": ["신혼"],
    }
    tags = set()
    text = title + " " + desc
    for keyword, tag_list in tag_map.items():
        if keyword in text:
            tags.update(tag_list)
    return list(tags)
