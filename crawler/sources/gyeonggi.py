"""
경기청년포털 (youth.gg.go.kr) 크롤러
- 경기도 한정 청년 정책 수집
- 카테고리: 일자리·창업 / 주거·복지 / 금융·법률 / 교육·자기개발
- 진행 중인 정책만 수집
"""
import re
import time
import requests
from bs4 import BeautifulSoup
from typing import Generator
from tenacity import retry, stop_after_attempt, wait_exponential

from crawler.models import Policy, PolicyType, AgeRange, IncomeCondition, LoanDetails


BASE_URL = "https://youth.gg.go.kr"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9",
    "Referer": BASE_URL,
}

# 카테고리 목록 → PolicyType 매핑
CATEGORIES = [
    {
        "url_path": "/gg/info/job-start-up.do",
        "name": "일자리·창업",
        "policy_type": PolicyType.EMPLOYMENT,
    },
    {
        "url_path": "/gg/info/housing-welfare.do",
        "name": "주거·복지",
        "policy_type": PolicyType.GRANT,
    },
    {
        "url_path": "/gg/info/finance-law.do",
        "name": "금융·법률",
        "policy_type": PolicyType.LOAN_GOVT,
    },
    {
        "url_path": "/gg/info/education-and-self-development.do",
        "name": "교육·자기개발",
        "policy_type": PolicyType.EDUCATION,
    },
]

# 지원 시·군 목록 (경기도 내 자치단체)
GG_CITIES = [
    "경기도", "수원시", "성남시", "의정부시", "안양시", "부천시", "광명시", "평택시",
    "동두천시", "안산시", "고양시", "과천시", "구리시", "남양주시", "오산시", "시흥시",
    "군포시", "의왕시", "하남시", "용인시", "파주시", "이천시", "안성시", "김포시",
    "화성시", "광주시", "양주시", "포천시", "여주시", "연천군", "가평군", "양평군",
]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
def _get_list_page(session: requests.Session, url_path: str, offset: int) -> BeautifulSoup:
    url = f"{BASE_URL}{url_path}?pager.offset={offset}&pagerLimit=8"
    resp = session.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=8))
def _get_detail_page(session: requests.Session, url_path: str, arc_no: str) -> BeautifulSoup:
    url = f"{BASE_URL}{url_path}?mode=view&arcNo={arc_no}"
    resp = session.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def _parse_list_items(soup: BeautifulSoup) -> list[dict]:
    """목록 페이지에서 기본 메타 추출"""
    items = []
    for a in soup.select("a[href*='arcNo']"):
        href = a.get("href", "")
        arc_no_match = re.search(r"arcNo=(\d+)", href)
        if not arc_no_match:
            continue
        arc_no = arc_no_match.group(1)

        li = a.find_parent("li") or a.find_parent("div")
        if not li:
            continue

        spans = [s.get_text(strip=True) for s in li.select("span, em") if s.get_text(strip=True)]

        # 상태 (진행/마감)
        status = spans[0] if spans else ""
        if status == "마감":
            continue  # 진행 중 정책만 수집

        # 시·군 (spans[1]), 카테고리 (spans[2])
        region_text = spans[1] if len(spans) > 1 else "경기도"

        # 제목 (마지막 a 태그 텍스트 or 마지막 span)
        full_text = li.get_text(separator="|", strip=True)
        parts = [p.strip() for p in full_text.split("|") if p.strip()]
        title = parts[-1] if parts else ""

        items.append({
            "arc_no": arc_no,
            "region_text": region_text,
            "title": title,
            "status": status,
        })
    return items


def _parse_detail(soup: BeautifulSoup, fallback_title: str, policy_type: PolicyType) -> dict:
    """상세 페이지에서 정책 정보 추출"""
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()

    main = soup.find("main") or soup.find("div", id="content") or soup.body
    text = main.get_text(separator="\n", strip=True) if main else soup.get_text(separator="\n", strip=True)

    # 제목: 카테고리 헤딩(h2 첫 번째)을 건너뛰고 실제 정책명 추출
    _cat_names = {"일자리·창업", "주거·복지", "금융·법률", "교육·자기개발"}
    title = fallback_title
    for h in soup.select("h1, h2, h3"):
        t = h.get_text(strip=True)
        if t and t not in _cat_names and len(t) > 2:
            title = t
            break

    # 신청기간
    period_match = re.search(r"신청기간\s*:?\s*([^\n]+(?:\n[^\n]+)?)", text)
    application_period = period_match.group(1).strip() if period_match else None

    # 지원대상 / 모집대상
    target_match = re.search(r"(?:지원|모집)대상\s*:?\s*([^\n]{10,300})", text)
    target_text = target_match.group(1).strip() if target_match else ""

    # 나이 추출
    age = _extract_age(target_text + " " + text[:500])

    # 소득 조건 추출
    income = _extract_income(text[:1000])

    # 지원내용
    content_match = re.search(r"지원내용\s*:?\s*([\s\S]{10,500}?)(?:\n신청방법|\n문의|\n바로가기|$)", text)
    description = content_match.group(1).strip() if content_match else target_text[:300]

    # 신청 URL (바로가기)
    apply_url = None
    for a in soup.select("a"):
        if "바로가기" in a.get_text() or "신청" in a.get_text():
            href = a.get("href", "")
            if href.startswith("http"):
                apply_url = href
                break

    # 문의
    contact_match = re.search(r"문의\s*:?\s*([^\n]{5,80})", text)
    contact = contact_match.group(1).strip() if contact_match else None

    # 태그
    tags = _auto_tags(title, description or "")
    tags.append("경기도")

    return {
        "title": title,
        "description": description,
        "application_period": application_period,
        "age": age,
        "income": income,
        "apply_url": apply_url,
        "contact": contact,
        "tags": tags,
    }


def _extract_age(text: str) -> AgeRange | None:
    # "만 19~34세" 또는 "만 19세 ~ 만 34세"
    range_match = re.search(r"만\s*(\d{1,2})\s*세?\s*[~\-]\s*만?\s*(\d{1,2})\s*세", text)
    if range_match:
        return AgeRange(min_age=int(range_match.group(1)), max_age=int(range_match.group(2)))
    # "만 X세 이하"
    upper_match = re.search(r"만\s*(\d{1,2})\s*세\s*이하", text)
    if upper_match:
        return AgeRange(min_age=15, max_age=int(upper_match.group(1)))
    # "19~39세" (숫자만)
    range2 = re.search(r"(\d{2})\s*[~\-]\s*(\d{2})\s*세", text)
    if range2:
        return AgeRange(min_age=int(range2.group(1)), max_age=int(range2.group(2)))
    return None


def _extract_income(text: str) -> IncomeCondition | None:
    # 중위소득 X% 이하
    median_match = re.search(r"중위소득\s*(\d+)\s*%\s*이하", text)
    if median_match:
        return IncomeCondition(
            max_income_ratio=int(median_match.group(1)) / 100,
            description=f"중위소득 {median_match.group(1)}% 이하",
        )
    # 연소득 X만원 이하
    income_match = re.search(r"연\s*소득\s*(\d+(?:,\d+)?)\s*만원\s*이하", text)
    if income_match:
        amount = int(income_match.group(1).replace(",", ""))
        return IncomeCondition(max_income=amount, description=f"연소득 {amount}만원 이하")
    return None


def _auto_tags(title: str, desc: str) -> list[str]:
    tag_map = {
        "취업": ["취업"],
        "창업": ["창업"],
        "일자리": ["일자리"],
        "주거": ["주거"],
        "전세": ["전세", "주거"],
        "월세": ["월세", "주거"],
        "대출": ["대출"],
        "지원금": ["지원금"],
        "장학": ["장학"],
        "교육": ["교육"],
        "청년": ["청년"],
        "신혼": ["신혼"],
        "저축": ["저축"],
        "금융": ["금융"],
        "법률": ["법률"],
    }
    tags: set[str] = set()
    text = title + " " + desc
    for kw, tag_list in tag_map.items():
        if kw in text:
            tags.update(tag_list)
    return list(tags)


def crawl_gyeonggi(max_pages_per_category: int = 10) -> Generator[Policy, None, None]:
    """
    경기청년포털에서 경기도 청년 정책 수집
    max_pages_per_category: 카테고리별 최대 페이지 수 (1페이지 = 8건)
    """
    session = requests.Session()

    for cat in CATEGORIES:
        url_path = cat["url_path"]
        cat_name = cat["name"]
        policy_type = cat["policy_type"]

        print(f"[gyeonggi] {cat_name} 크롤링 시작...")
        cat_count = 0

        for page in range(max_pages_per_category):
            offset = page * 8
            try:
                list_soup = _get_list_page(session, url_path, offset)
                items = _parse_list_items(list_soup)

                if not items:
                    break

                for item in items:
                    arc_no = item["arc_no"]
                    region_text = item["region_text"]
                    fallback_title = item["title"]

                    # 경기도 내 지역만 수집
                    region_label = region_text if region_text in GG_CITIES else "경기도"

                    try:
                        detail_soup = _get_detail_page(session, url_path, arc_no)
                        detail = _parse_detail(detail_soup, fallback_title, policy_type)
                        time.sleep(0.4)
                    except Exception as e:
                        print(f"[gyeonggi] 상세 오류 arcNo={arc_no}: {e}")
                        detail = {
                            "title": fallback_title,
                            "description": None,
                            "application_period": None,
                            "age": None,
                            "income": None,
                            "apply_url": None,
                            "contact": None,
                            "tags": ["경기도", cat_name],
                        }

                    policy = Policy(
                        id=f"gg_{arc_no}",
                        name=detail["title"] or fallback_title,
                        source="경기청년포털",
                        source_url=f"{BASE_URL}{url_path}?mode=view&arcNo={arc_no}",
                        policy_type=policy_type,
                        description=detail["description"],
                        age=detail["age"],
                        income=detail["income"],
                        regions=[region_label],
                        application_url=detail["apply_url"],
                        application_period=detail["application_period"],
                        contact=detail["contact"],
                        tags=detail["tags"],
                    )
                    yield policy
                    cat_count += 1

                time.sleep(0.5)

            except Exception as e:
                print(f"[gyeonggi] {cat_name} 페이지 {page + 1} 오류: {e}")
                break

        print(f"[gyeonggi] {cat_name} 완료: {cat_count}건")


# ---------------------------------------------------------------------------
# 경기도 주요 정적 정책 (파일 기반, 공식 조건 기준)
# 출처: 경기주거복지포털(housing.gg.go.kr), 잡아바(apply.jobaba.net), gg.go.kr
# ---------------------------------------------------------------------------
_GG_STATIC_POLICIES: list[Policy] = [
    # ── 경기도 청년기본소득 ──────────────────────────────────────
    Policy(
        id="gg_static_basic_income",
        name="경기도 청년기본소득",
        source="경기도",
        source_url="https://apply.jobaba.net",
        policy_type=PolicyType.GRANT,
        description="경기도에 1년 이상 주민등록을 둔 만 24세 청년에게 분기별 25만원(연 100만원) 경기지역화폐를 지원합니다. 소득·재산 무관.",
        age=AgeRange(min_age=24, max_age=24),
        regions=["경기도"],
        application_url="https://apply.jobaba.net",
        tags=["청년기본소득", "지역화폐", "청년", "경기도", "지원금"],
    ),
    # ── 경기도 대학생 학자금 대출이자 지원 ──────────────────────
    Policy(
        id="gg_static_student_loan_interest",
        name="경기도 대학생 학자금 대출이자 지원",
        source="경기도",
        source_url="https://www.gg.go.kr",
        policy_type=PolicyType.GRANT,
        description="경기도 거주 대학생·대학원생·미취업 졸업생(졸업 후 2년 이내) 대상 한국장학재단 학자금 대출이자 전액 지원.",
        age=AgeRange(min_age=19, max_age=34),
        income=IncomeCondition(max_income=5000, description="연소득 5,000만원 이하(중위소득 200% 이하)"),
        regions=["경기도"],
        application_url="https://apply.jobaba.net",
        tags=["학자금", "이자지원", "대학생", "청년", "경기도", "교육", "지원금"],
    ),
    # ── 경기도 청년 노동자 복지포인트 ───────────────────────────
    Policy(
        id="gg_static_worker_welfare_point",
        name="경기도 중소기업 청년 노동자 지원사업 (복지포인트)",
        source="경기도일자리재단",
        source_url="https://youth.jobaba.net",
        policy_type=PolicyType.GRANT,
        description="경기도 소재 중소기업에 재직 중인 만 18~34세 청년 노동자에게 연간 최대 120만원 복지포인트(문화·여가·자기개발 사용)를 지원합니다.",
        age=AgeRange(min_age=18, max_age=34),
        income=IncomeCondition(max_income=3600, description="월 급여 300만원 이하"),
        regions=["경기도"],
        application_url="https://youth.jobaba.net",
        tags=["복지포인트", "청년", "노동자", "중소기업", "경기도", "지원금", "취업"],
    ),
    # ── 경기 청년 매입임대 ───────────────────────────────────────
    Policy(
        id="gg_static_youth_buy_rent",
        name="경기 청년 매입임대주택",
        source="경기주거복지포털",
        source_url="https://housing.gg.go.kr/html/51100.do",
        policy_type=PolicyType.LOAN_HOUSING,
        description="경기도가 매입한 주택을 저소득층 대학생·취업준비생·청년(19~39세)에게 시중시세 40~50% 수준으로 임대. 임대기간 최장 6년.",
        age=AgeRange(min_age=19, max_age=39),
        regions=["경기도"],
        application_url="https://housing.gg.go.kr/html/51100.do",
        tags=["임대주택", "매입임대", "주거", "청년", "경기도"],
    ),
    # ── 경기행복주택 ─────────────────────────────────────────────
    Policy(
        id="gg_static_happy_house",
        name="경기행복주택 (청년·신혼부부)",
        source="경기주거복지포털",
        source_url="https://housing.gg.go.kr/html/51200.do",
        policy_type=PolicyType.LOAN_HOUSING,
        description="대학생·청년·신혼부부 대상 경기도 특화 공공임대주택. 시중시세의 60~80% 수준, 대중교통 요지·직주근접 입지. 2년마다 재계약(최장 6~20년).",
        age=AgeRange(min_age=19, max_age=39),
        regions=["경기도"],
        application_url="https://apply.gh.or.kr",
        tags=["행복주택", "공공임대", "주거", "청년", "신혼", "경기도"],
    ),
    # ── 청년 기존주택 전세임대 ───────────────────────────────────
    Policy(
        id="gg_static_youth_jeonse_rent",
        name="경기 청년 기존주택 전세임대",
        source="경기주거복지포털",
        source_url="https://housing.gg.go.kr/html/51400.do",
        policy_type=PolicyType.LOAN_HOUSING,
        description="무주택 대학생·취업준비생·만 19~39세 청년 대상. 기존주택을 전세 계약 후 저렴하게 재임대. 1순위: 생계·의료·주거급여 수급자 가구.",
        age=AgeRange(min_age=19, max_age=39),
        regions=["경기도"],
        application_url="https://housing.gg.go.kr/html/51400.do",
        tags=["전세임대", "전세", "주거", "청년", "경기도", "대출"],
    ),
    # ── GH 공공임대·청약 ─────────────────────────────────────────
    Policy(
        id="gg_static_gh_apply",
        name="GH 경기주택도시공사 공공임대·청약",
        source="GH 경기주택도시공사",
        source_url="https://apply.gh.or.kr",
        policy_type=PolicyType.LOAN_HOUSING,
        description="경기도 공공임대주택(청년·신혼·일반) 청약 및 임대 신청 통합 플랫폼. 경기행복주택, 영구임대, 국민임대 등 신청.",
        age=AgeRange(min_age=19, max_age=39),
        regions=["경기도"],
        application_url="https://apply.gh.or.kr",
        tags=["공공임대", "청약", "주거", "청년", "신혼", "경기도"],
    ),
]


def crawl_gyeonggi_static() -> list[Policy]:
    """파일 기반 경기도 주요 고정 정책 반환"""
    print(f"[gyeonggi_static] 정적 정책 {len(_GG_STATIC_POLICIES)}건 로드")
    return list(_GG_STATIC_POLICIES)
