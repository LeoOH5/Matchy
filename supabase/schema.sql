-- 청년 정책 테이블
create table if not exists policies (
  id text primary key,
  name text not null,
  source text not null,
  source_url text,
  policy_type text not null,
  description text,
  age_min integer,
  age_max integer,
  income_max integer,
  income_ratio real,
  income_desc text,
  regions jsonb default '[]',
  loan_rate_min real,
  loan_rate_max real,
  loan_amount_max integer,
  loan_period_max integer,
  loan_collateral text,
  grant_amount integer,
  application_url text,
  application_period text,
  tags jsonb default '[]',
  crawled_at timestamptz default now(),
  is_active boolean default true
);

-- 검색용 인덱스
create index if not exists idx_policies_type on policies(policy_type);
create index if not exists idx_policies_active on policies(is_active);
create index if not exists idx_policies_age on policies(age_min, age_max);
create index if not exists idx_policies_income on policies(income_max);
create index if not exists idx_policies_rate on policies(loan_rate_min);

-- 전문 검색 인덱스
create index if not exists idx_policies_name_fts
  on policies using gin(to_tsvector('simple', name));

-- RLS 비활성화 (공개 데이터)
alter table policies disable row level security;

-- 시드 데이터: 주택도시기금
insert into policies values
('youth_jeonse', '청년전용 버팀목전세자금', '주택도시기금',
 'https://nhuf.molit.go.kr/FP/NH05/NH0503/NH050301/selectNH0503010000.jsp',
 '주거대출',
 '만 19~34세 무주택 세대주 대상 전세자금 대출. 연소득 5천만원 이하.',
 19, 34, 5000, null, '연소득 5천만원 이하',
 '[]', 1.8, 2.7, 10000, 120, '한국주택금융공사 보증',
 null,
 'https://nhuf.molit.go.kr/FP/NH05/NH0503/NH050301/selectNH0503010000.jsp',
 null, '["전세","주거","청년","대출","버팀목"]', now(), true),

('sme_youth_jeonse', '중소기업취업청년 전월세보증금대출', '주택도시기금',
 'https://nhuf.molit.go.kr/FP/NH05/NH0503/NH050302/selectNH0503020000.jsp',
 '주거대출',
 '중소·중견기업 재직 만 19~34세 청년 대상. 연소득 3500만원 이하.',
 19, 34, 3500, null, '연소득 3500만원 이하',
 '[]', 1.2, 1.2, 10000, 120, '한국주택금융공사 보증',
 null,
 'https://nhuf.molit.go.kr/FP/NH05/NH0503/NH050302/selectNH0503020000.jsp',
 null, '["전세","월세","청년","대출","중소기업"]', now(), true),

('youth_monthly_rent', '청년전용 보증부월세대출', '주택도시기금',
 'https://nhuf.molit.go.kr/FP/NH05/NH0503/NH050303/selectNH0503030000.jsp',
 '주거대출',
 '만 19~34세 무주택 단독세대주 대상 월세보증금+월세 대출. 연소득 2천만원 이하.',
 19, 34, 2000, null, '연소득 2천만원 이하',
 '[]', 1.3, 2.1, 3000, 24, '한국주택금융공사 보증',
 null,
 'https://nhuf.molit.go.kr/FP/NH05/NH0503/NH050303/selectNH0503030000.jsp',
 null, '["월세","주거","청년","대출"]', now(), true),

('newlywed_jeonse', '신혼부부전용 전세자금', '주택도시기금',
 'https://nhuf.molit.go.kr/FP/NH05/NH0503/NH050304/selectNH0503040000.jsp',
 '주거대출',
 '혼인 7년 이내 무주택 세대주 대상. 합산 연소득 6천만원 이하.',
 19, 45, 6000, null, '부부합산 연소득 6천만원 이하',
 '[]', 1.5, 2.4, 30000, 120, '한국주택금융공사 보증',
 null,
 'https://nhuf.molit.go.kr/FP/NH05/NH0503/NH050304/selectNH0503040000.jsp',
 null, '["전세","신혼","대출","주거"]', now(), true)
on conflict(id) do update set
  loan_rate_min = excluded.loan_rate_min,
  loan_rate_max = excluded.loan_rate_max,
  crawled_at = now();

-- 시드 데이터: 시중은행
insert into policies values
('kb_youth_jeonse', 'KB 청년전세대출', 'KB국민은행',
 'https://obank.kbstar.com/quics?page=C101351',
 '주거대출', null,
 19, 34, null, null, null,
 '[]', 2.0, 4.5, 20000, 120, null,
 null, 'https://obank.kbstar.com/quics?page=C101351',
 null, '["전세","청년","KB국민은행","대출"]', now(), true),

('shinhan_youth_jeonse', '신한 청년대출', '신한은행',
 'https://www.shinhan.com/hpe/index.jsp#050101010000',
 '주거대출', null,
 19, 34, null, null, null,
 '[]', 3.0, 5.0, 25000, 120, null,
 null, 'https://www.shinhan.com/hpe/index.jsp#050101010000',
 null, '["청년","신한은행","대출","주거"]', now(), true),

('woori_youth', '우리 청년 전월세대출', '우리은행',
 'https://spot.wooribank.com/pot/Dream?withyou=POLON0029',
 '주거대출', null,
 19, 34, null, null, null,
 '[]', 2.8, 4.8, 15000, 120, null,
 null, 'https://spot.wooribank.com/pot/Dream?withyou=POLON0029',
 null, '["전세","월세","청년","우리은행","대출"]', now(), true),

('ibk_youth_jeonse', 'IBK 청년전세대출', 'IBK기업은행',
 'https://www.ibk.co.kr/renew/main.ibk',
 '주거대출', null,
 19, 34, null, null, null,
 '[]', 2.5, 4.2, 20000, 120, null,
 null, 'https://www.ibk.co.kr/renew/main.ibk',
 null, '["전세","청년","IBK기업은행","대출"]', now(), true),

('kakao_youth_jeonse', '카카오뱅크 청년 전월세보증금 대출', '카카오뱅크',
 'https://www.kakaobank.com/products/lease',
 '주거대출', null,
 19, 34, null, null, null,
 '[]', 2.1, 3.8, 25000, 120, null,
 null, 'https://www.kakaobank.com/products/lease',
 null, '["전세","월세","청년","카카오뱅크","대출","인터넷은행"]', now(), true)
on conflict(id) do update set
  loan_rate_min = excluded.loan_rate_min,
  loan_rate_max = excluded.loan_rate_max,
  crawled_at = now();
