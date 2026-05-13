"use client";

import { useEffect, useRef, useState } from "react";
import { UserProfile } from "@/types";

/* ── 질문 정의 ── */
type QType = "text" | "year" | "income" | "chips" | "region" | "counter" | "multi";

interface QDef {
  id: string;
  q: string;
  type: QType;
  opts?: { value: string; label: string; emoji?: string }[];
  skip?: (a: Answers) => boolean;
  fmt: (v: unknown) => string;
}

type Answers = Record<string, unknown>;

const REGIONS = [
  "서울","경기","인천","부산","대구",
  "광주","대전","울산","세종","강원",
  "충북","충남","전북","전남","경북","경남","제주",
];

const QS: QDef[] = [
  {
    id: "name", q: "안녕하세요!\n이름이 어떻게 되세요?", type: "text",
    fmt: (v) => String(v),
  },
  {
    id: "birth_year", q: "몇 년생이세요?", type: "year",
    fmt: (v) => `${v}년생 · 만 ${2026 - Number(v) + 1}세`,
  },
  {
    id: "gender", q: "성별을 알려주세요", type: "chips",
    opts: [{ value: "male", label: "남성", emoji: "👨" }, { value: "female", label: "여성", emoji: "👩" }],
    fmt: (v) => v === "male" ? "남성" : "여성",
  },
  {
    id: "region", q: "어디에 살고 계세요?", type: "region",
    fmt: (v) => String(v),
  },
  {
    id: "marital_status", q: "혼인 여부를 알려주세요", type: "chips",
    opts: [
      { value: "single", label: "미혼", emoji: "🙋" },
      { value: "newlywed", label: "신혼부부", emoji: "💑" },
      { value: "married", label: "기혼", emoji: "👨‍👩‍👦" },
    ],
    fmt: (v) => ({ single: "미혼", newlywed: "신혼부부", married: "기혼" } as Record<string,string>)[String(v)],
  },
  {
    id: "income", q: "연 소득이 얼마인가요?\n(세전 기준)", type: "income",
    fmt: (v) => `연 ${Number(v).toLocaleString()}만원`,
  },
  {
    id: "employment_status", q: "어떤 일을 하고 계세요?", type: "chips",
    opts: [
      { value: "employed",   label: "직장인",   emoji: "💼" },
      { value: "freelance",  label: "프리랜서", emoji: "💻" },
      { value: "student",    label: "학생",     emoji: "📚" },
      { value: "unemployed", label: "미취업",   emoji: "🔍" },
    ],
    fmt: (v) => ({ employed:"직장인", freelance:"프리랜서", student:"학생", unemployed:"미취업" } as Record<string,string>)[String(v)],
  },
  {
    id: "employment_type", q: "직장 규모는 어떻게 되세요?", type: "chips",
    skip: (a) => a.employment_status !== "employed",
    opts: [
      { value: "sme",    label: "중소·중견기업",   emoji: "🏢" },
      { value: "large",  label: "대기업",           emoji: "🏙" },
      { value: "public", label: "공공기관·공무원",  emoji: "🏛" },
    ],
    fmt: (v) => ({ sme:"중소·중견기업", large:"대기업", public:"공공기관" } as Record<string,string>)[String(v)],
  },
  {
    id: "housing_type", q: "지금 어떻게 살고 계세요?", type: "chips",
    opts: [
      { value: "monthly", label: "월세",      emoji: "🏠" },
      { value: "jeonse",  label: "전세",      emoji: "🏡" },
      { value: "own",     label: "자가",      emoji: "🔑" },
      { value: "parents", label: "부모님 댁", emoji: "👨‍👩‍👧" },
    ],
    fmt: (v) => ({ monthly:"월세", jeonse:"전세", own:"자가", parents:"부모님 댁" } as Record<string,string>)[String(v)],
  },
  {
    id: "household_members", q: "가구원은 몇 명인가요?", type: "counter",
    fmt: (v) => `${v}명`,
  },
  {
    id: "purpose", q: "어떤 지원을 찾고 계세요?", type: "multi",
    opts: [
      { value: "전세대출",  label: "전세 대출",      emoji: "🏠" },
      { value: "월세대출",  label: "월세 보증금",    emoji: "🏢" },
      { value: "원룸대출",  label: "원룸 대출",      emoji: "🛏" },
      { value: "창업지원",  label: "창업 지원금",    emoji: "🚀" },
      { value: "취업지원",  label: "취업 지원",      emoji: "💼" },
      { value: "교육비",    label: "교육비 지원",    emoji: "📚" },
    ],
    fmt: (v) => (v as string[]).join(" · "),
  },
];

/* ── 메인 컴포넌트 ── */

interface Props {
  onSubmit: (p: UserProfile) => void;
  loading: boolean;
}

export default function ProfileForm({ onSubmit, loading }: Props) {
  const [answers, setAnswers]     = useState<Answers>({});
  const [step, setStep]           = useState(0);
  const [text, setText]           = useState("");
  const [counter, setCounter]     = useState(1);
  const [multi, setMulti]         = useState<string[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  const visible = QS.filter((q) => !q.skip?.(answers));
  const done    = visible.slice(0, step);
  const cur     = visible[step] ?? null;
  const isLast  = step === visible.length - 1;
  const pct     = visible.length ? Math.round((step / visible.length) * 100) : 0;

  useEffect(() => {
    // 새 질문이 나올 때 스크롤 내리기
    setTimeout(() => {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
    }, 50);
  }, [step]);

  const advance = (id: string, value: unknown) => {
    const next = { ...answers, [id]: value };
    setAnswers(next);
    const nextVisible = QS.filter((q) => !q.skip?.(next));
    const nextStep = nextVisible.findIndex((q) => q.id === id) + 1;
    if (nextStep < nextVisible.length) {
      const nq = nextVisible[nextStep];
      setText("");
      setCounter(1);
      setMulti([]);
      setStep(nextStep);
    } else {
      onSubmit(next as unknown as UserProfile);
    }
  };

  const confirmText = () => {
    if (!cur) return;
    const t = text.trim();
    if (!t) return;
    if (cur.type === "year") {
      const y = parseInt(t);
      if (isNaN(y) || y < 1960 || y > 2007) return;
      advance(cur.id, y);
    } else if (cur.type === "income") {
      const n = parseInt(t.replace(/,/g, ""));
      if (isNaN(n) || n < 0) return;
      advance(cur.id, n);
    } else {
      advance(cur.id, t);
    }
  };

  return (
    <div className="flex flex-col" style={{ height: "calc(100dvh - 57px)" }}>
      {/* 진행 바 */}
      <div className="h-0.5 bg-gray-100 shrink-0">
        <div className="h-full bg-blue-500 transition-all duration-500" style={{ width: `${pct}%` }} />
      </div>

      {/* 스크롤 영역 */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto overscroll-contain">
        <div className="max-w-md mx-auto px-5 pt-8 pb-10 space-y-8">

          {/* 답변 완료된 항목들 */}
          {done.map((q) => (
            <div key={q.id} className="space-y-1">
              <p className="text-sm text-gray-400 leading-snug">
                {q.q.replace(/\n/g, " ")}
              </p>
              <span className="inline-flex items-center gap-1.5 bg-gray-100 text-gray-600 text-sm font-semibold px-3.5 py-1.5 rounded-full">
                <span className="text-blue-400 text-xs">✓</span>
                {q.fmt(answers[q.id])}
              </span>
            </div>
          ))}

          {/* 현재 질문 — 아래서 슬라이드업 */}
          {cur && (
            <div key={cur.id} className="space-y-5" style={{ animation: "qIn .28s cubic-bezier(.22,1,.36,1)" }}>
              {/* 질문 텍스트 */}
              <h2 className="text-2xl font-bold text-gray-900 leading-snug whitespace-pre-line">
                {cur.q}
              </h2>

              {/* ── 입력 UI ── */}

              {/* 텍스트 */}
              {cur.type === "text" && (
                <div className="flex gap-2">
                  <input
                    autoFocus
                    className="flex-1 bg-gray-50 border border-gray-200 rounded-2xl px-4 py-3.5 text-base outline-none focus:border-blue-400 focus:bg-white transition-colors"
                    placeholder="홍길동"
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && confirmText()}
                  />
                  <button
                    onClick={confirmText}
                    disabled={!text.trim()}
                    className="px-5 rounded-2xl bg-blue-600 disabled:bg-gray-200 text-white disabled:text-gray-400 font-bold transition-colors"
                  >확인</button>
                </div>
              )}

              {/* 연도 */}
              {cur.type === "year" && (
                <div className="space-y-2">
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <input
                        autoFocus
                        type="number"
                        className="w-full bg-gray-50 border border-gray-200 rounded-2xl px-4 py-3.5 text-base outline-none focus:border-blue-400 focus:bg-white transition-colors"
                        placeholder="1999"
                        min={1960} max={2007}
                        value={text}
                        onChange={(e) => setText(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && confirmText()}
                      />
                    </div>
                    <button
                      onClick={confirmText}
                      disabled={!text}
                      className="px-5 rounded-2xl bg-blue-600 disabled:bg-gray-200 text-white disabled:text-gray-400 font-bold transition-colors"
                    >확인</button>
                  </div>
                  {text && !isNaN(parseInt(text)) && parseInt(text) >= 1960 && parseInt(text) <= 2007 && (
                    <p className="text-sm text-blue-500 pl-1 font-medium">
                      만 {2026 - parseInt(text) + 1}세
                    </p>
                  )}
                </div>
              )}

              {/* 소득 */}
              {cur.type === "income" && (
                <div className="space-y-2">
                  <div className="flex gap-2 items-center">
                    <input
                      autoFocus
                      type="number"
                      className="flex-1 bg-gray-50 border border-gray-200 rounded-2xl px-4 py-3.5 text-base outline-none focus:border-blue-400 focus:bg-white transition-colors"
                      placeholder="3000"
                      min={0}
                      value={text}
                      onChange={(e) => setText(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && confirmText()}
                    />
                    <span className="text-gray-500 font-medium shrink-0">만원</span>
                    <button
                      onClick={confirmText}
                      disabled={!text}
                      className="px-5 py-3.5 rounded-2xl bg-blue-600 disabled:bg-gray-200 text-white disabled:text-gray-400 font-bold transition-colors"
                    >확인</button>
                  </div>
                  {text && !isNaN(parseInt(text)) && (
                    <p className="text-sm text-blue-500 pl-1 font-medium">
                      월 약 {Math.round(parseInt(text) / 12).toLocaleString()}만원
                    </p>
                  )}
                </div>
              )}

              {/* 칩 (단일 선택 → 즉시 진행) */}
              {cur.type === "chips" && (
                <div className="flex flex-wrap gap-2">
                  {cur.opts?.map((o) => (
                    <button
                      key={o.value}
                      onClick={() => advance(cur.id, o.value)}
                      className="flex items-center gap-2 px-5 py-3 rounded-2xl border-2 border-gray-200 hover:border-blue-500 hover:bg-blue-50 text-gray-700 font-semibold text-sm transition-all active:scale-95"
                    >
                      {o.emoji && <span>{o.emoji}</span>}
                      {o.label}
                    </button>
                  ))}
                </div>
              )}

              {/* 지역 그리드 */}
              {cur.type === "region" && (
                <div className="grid grid-cols-4 gap-2">
                  {REGIONS.map((r) => (
                    <button
                      key={r}
                      onClick={() => advance(cur.id, r)}
                      className="py-2.5 rounded-xl border-2 border-gray-200 hover:border-blue-500 hover:bg-blue-50 text-sm font-semibold text-gray-700 transition-all active:scale-95"
                    >
                      {r}
                    </button>
                  ))}
                </div>
              )}

              {/* 카운터 */}
              {cur.type === "counter" && (
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-5 bg-gray-50 rounded-2xl px-6 py-4">
                    <button
                      onClick={() => setCounter((c) => Math.max(1, c - 1))}
                      className="w-9 h-9 rounded-full bg-white border border-gray-200 hover:bg-gray-100 text-xl font-bold text-gray-600 shadow-sm transition-colors"
                    >−</button>
                    <span className="text-2xl font-bold text-gray-800 w-6 text-center">{counter}</span>
                    <button
                      onClick={() => setCounter((c) => Math.min(8, c + 1))}
                      className="w-9 h-9 rounded-full bg-white border border-gray-200 hover:bg-gray-100 text-xl font-bold text-gray-600 shadow-sm transition-colors"
                    >+</button>
                  </div>
                  <span className="text-gray-500">명</span>
                  <button
                    onClick={() => advance(cur.id, counter)}
                    className="ml-auto px-6 py-3.5 rounded-2xl bg-blue-600 text-white font-bold transition-colors"
                  >확인</button>
                </div>
              )}

              {/* 다중 선택 */}
              {cur.type === "multi" && (
                <div className="space-y-3">
                  <div className="grid grid-cols-2 gap-2">
                    {cur.opts?.map((o) => {
                      const on = multi.includes(o.value);
                      return (
                        <button
                          key={o.value}
                          onClick={() => setMulti((p) => on ? p.filter((v) => v !== o.value) : [...p, o.value])}
                          className={`flex items-center gap-2 px-4 py-3 rounded-2xl border-2 text-sm font-semibold transition-all active:scale-95 ${
                            on
                              ? "border-blue-500 bg-blue-50 text-blue-700"
                              : "border-gray-200 text-gray-600 hover:border-blue-300"
                          }`}
                        >
                          <span>{o.emoji}</span>{o.label}
                        </button>
                      );
                    })}
                  </div>
                  <button
                    onClick={() => { if (multi.length) advance(cur.id, multi); }}
                    disabled={multi.length === 0 || loading}
                    className="w-full py-4 rounded-2xl bg-blue-600 disabled:bg-gray-200 text-white disabled:text-gray-400 font-bold text-base transition-colors flex items-center justify-center gap-2"
                  >
                    {loading && (
                      <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                      </svg>
                    )}
                    {isLast ? "정책 찾기 🔍" : "다음"}
                  </button>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

    </div>
  );
}
