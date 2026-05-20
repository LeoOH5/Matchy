<div align="center">

# 🎯 Matchy

### 내게 딱 맞는 청년 정책·대출을 한 번에 찾아드려요

[![배포](https://img.shields.io/badge/배포-matchyapp.vercel.app-blue?style=for-the-badge&logo=vercel)](https://matchyapp.vercel.app/)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-15-000000?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org)

**[→ 지금 바로 사용해보기](https://matchyapp.vercel.app/)**

</div>

---

## 📺 소개 영상

<video src="matchy-promo.mp4" autoplay loop muted playsinline width="100%"></video>

> 청년 정책이 너무 복잡하게 흩어져 있나요? Matchy가 내 조건에 맞는 상품을 금리 낮은 순으로 즉시 정리해드립니다.

---

## ✨ 주요 기능

| 기능 | 설명 |
|---|---|
| 🏛 **정부 정책 통합** | 청년정책포털, 주택도시기금 상품 한번에 조회 |
| 🏦 **시중은행 포함** | KB·신한·우리·카카오뱅크 대출 상품 포함 |
| ⚡ **즉시 매칭** | 나이·소득·지역·고용형태 입력 후 바로 결과 확인 |
| 📊 **금리 낮은 순 정렬** | 조건에 맞는 최저금리 상품부터 자동 정렬 |
| 🔓 **회원가입 없음** | 로그인·회원가입 없이 바로 사용 가능 |

---

## 🖥 서비스 화면

### 1. 내 조건 입력
나이, 연소득, 거주 지역, 고용형태, 혼인상태, 희망 지원 목적을 입력합니다.

### 2. 즉시 매칭
입력한 조건을 기반으로 정부 정책 + 시중은행 상품을 필터링해 **금리 낮은 순**으로 보여줍니다.

### 3. 상품 비교
- 정부대출 / 은행대출 / 주거대출 / 지원금 카테고리 필터
- 금리 낮은 순 / 한도 높은 순 정렬 전환
- 최저금리 추천 배너

---

## 🗂 매칭 가능한 상품 유형

```
정부지원금    청년도약계좌, 청년내일채움공제, 청년일자리도약장려금 등
정부대출      중기청 청년전세대출, 버팀목 전세자금, 주거안정월세대출 등
주거대출      청년주택드림청약, 신혼부부전용전세자금 등
은행대출      카카오뱅크·KB·신한·우리 전세/생활안정 대출 등
취업지원      국민취업지원제도, 청년창업사관학교 등
```

---

## 🧑‍💻 기술 스택

```
Frontend     Next.js 15 · TypeScript · Tailwind CSS
Backend      FastAPI · Python 3.11 · Pydantic
Database     SQLite (로컬) · Supabase (프로덕션)
Crawler      Python · httpx · BeautifulSoup
Infra        Vercel (프론트엔드) · 크롤러 자동화
```

---

## 🚀 로컬 실행

### 사전 요건
- Python 3.11+
- Node.js 18+
- FFmpeg (선택)

### 1. 저장소 클론
```bash
git clone https://github.com/<your-username>/Matchy.git
cd Matchy
```

### 2. 백엔드 실행
```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt

python run_crawler.py            # 정책 데이터 수집
uvicorn api.main:app --reload    # API 서버 실행 (port 8000)
```

### 3. 프론트엔드 실행
```bash
cd frontend
cp .env.example .env.local       # 환경변수 설정
npm install
npm run dev                      # http://localhost:3000
```

### 또는 한번에 실행
```bash
./start_servers.sh
```

---

## 📡 API 엔드포인트

| 메서드 | 경로 | 설명 |
|---|---|---|
| `POST` | `/api/match` | 프로필 기반 정책 매칭 |
| `GET` | `/api/policies` | 정책 목록 검색 |
| `GET` | `/api/stats` | 데이터 통계 |

### 매칭 요청 예시
```json
POST /api/match
{
  "name": "홍길동",
  "birth_year": 1999,
  "gender": "male",
  "income": 3600,
  "region": "서울",
  "employment_status": "employed",
  "employment_type": "sme",
  "housing_type": "monthly",
  "marital_status": "single",
  "purpose": ["전세대출", "취업지원"]
}
```

---

## 📁 프로젝트 구조

```
Matchy/
├── api/
│   └── main.py          # FastAPI 라우터
├── crawler/
│   ├── models.py        # Pydantic 데이터 모델
│   └── storage.py       # SQLite 저장/검색
├── frontend/
│   └── src/
│       ├── app/         # Next.js App Router
│       ├── components/  # ProfileForm, PolicyCard, ResultsView
│       └── lib/         # API 클라이언트
├── supabase/
│   └── schema.sql       # DB 스키마
└── run_crawler.py       # 크롤러 진입점
```

---

## 🌐 배포

**프론트엔드**: [https://matchyapp.vercel.app/](https://matchyapp.vercel.app/) (Vercel)

환경변수 설정:
```
NEXT_PUBLIC_API_URL=<FastAPI 서버 URL>
NEXT_PUBLIC_SUPABASE_URL=<Supabase 프로젝트 URL>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<Supabase anon key>
```

---

<div align="center">

© 2026 Matchy · 실제 금리·조건은 기관별로 변동될 수 있습니다. 신청 전 반드시 공식 사이트를 확인하세요.

</div>
