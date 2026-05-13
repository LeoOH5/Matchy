from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
from datetime import datetime


class PolicyType(str, Enum):
    GRANT = "지원금"           # 보조금/지원금
    LOAN_GOVT = "정부대출"      # 정부/공공 대출
    LOAN_BANK = "은행대출"      # 시중은행 대출
    LOAN_HOUSING = "주거대출"   # 주거 관련 대출
    EDUCATION = "교육"          # 교육비 지원
    EMPLOYMENT = "취업"         # 취업 지원
    OTHER = "기타"


class AgeRange(BaseModel):
    min_age: Optional[int] = None
    max_age: Optional[int] = None


class IncomeCondition(BaseModel):
    max_income: Optional[int] = None          # 만원 단위
    max_income_ratio: Optional[float] = None  # 중위소득 대비 비율 (예: 0.6 = 60%)
    description: Optional[str] = None


class LoanDetails(BaseModel):
    min_rate: Optional[float] = None    # 최저 금리 (%)
    max_rate: Optional[float] = None    # 최고 금리 (%)
    max_amount: Optional[int] = None    # 최대 대출금액 (만원)
    max_period: Optional[int] = None    # 최대 대출 기간 (개월)
    collateral: Optional[str] = None    # 담보 조건
    repayment_method: Optional[str] = None  # 상환 방식


class Policy(BaseModel):
    id: Optional[str] = None
    name: str
    source: str                          # 크롤링 출처 기관
    source_url: Optional[str] = None
    policy_type: PolicyType
    description: Optional[str] = None

    # 대상 조건
    age: Optional[AgeRange] = None
    income: Optional[IncomeCondition] = None
    regions: list[str] = Field(default_factory=list)  # 빈 리스트 = 전국

    # 대출 상품인 경우
    loan: Optional[LoanDetails] = None

    # 지원금인 경우
    grant_amount: Optional[int] = None   # 만원 단위
    grant_description: Optional[str] = None

    # 신청 정보
    application_url: Optional[str] = None
    application_period: Optional[str] = None
    deadline: Optional[datetime] = None
    contact: Optional[str] = None

    # 태그 (검색용)
    tags: list[str] = Field(default_factory=list)

    crawled_at: datetime = Field(default_factory=datetime.now)
    is_active: bool = True
