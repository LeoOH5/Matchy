"use client";
import { useState } from "react";
import { MatchResult, Policy, UserProfile } from "@/types";
import PolicyCard from "./PolicyCard";

const TYPE_FILTERS = [
  { value: "", label: "전체" },
  { value: "주거대출", label: "주거대출" },
  { value: "정부대출", label: "정부대출" },
  { value: "은행대출", label: "은행대출" },
  { value: "지원금", label: "지원금" },
];

interface Props {
  result: MatchResult;
  profile: UserProfile;
  onReset: () => void;
}

export default function ResultsView({ result, profile, onReset }: Props) {
  const [typeFilter, setTypeFilter] = useState("");
  const [sortBy, setSortBy] = useState<"rate" | "amount">("rate");

  const filtered = result.policies
    .filter((p) => !typeFilter || p.policy_type === typeFilter)
    .sort((a, b) => {
      if (sortBy === "rate") {
        return (a.loan_rate_min ?? 99) - (b.loan_rate_min ?? 99);
      }
      return (b.loan_amount_max ?? 0) - (a.loan_amount_max ?? 0);
    });

  const bestRate = filtered.find((p) => p.loan_rate_min != null);

  return (
    <div className="w-full max-w-2xl mx-auto">
      {/* 결과 요약 헤더 */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-500 rounded-2xl p-6 mb-6 text-white">
        <div className="flex items-center justify-between mb-4">
          <div>
            <p className="text-blue-100 text-sm mb-1">
              {profile.name}님 (만 {result.age}세 · {profile.region})
            </p>
            <h2 className="text-2xl font-bold">
              {result.matched_count}개의 상품을 찾았어요
            </h2>
          </div>
          <button onClick={onReset}
            className="text-blue-100 hover:text-white text-sm border border-blue-400 hover:border-white px-3 py-1.5 rounded-lg transition-colors">
            다시 검색
          </button>
        </div>

        {bestRate && bestRate.loan_rate_min != null && (
          <div className="bg-white/20 rounded-xl p-3 flex items-center gap-3">
            <span className="text-2xl">🏆</span>
            <div>
              <p className="text-blue-100 text-xs">최저 금리 추천</p>
              <p className="font-bold">{bestRate.name}</p>
              <p className="text-blue-100 text-sm">연 {bestRate.loan_rate_min}% ~</p>
            </div>
          </div>
        )}
      </div>

      {/* 필터 & 정렬 */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 mb-5">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex gap-2 flex-wrap flex-1">
            {TYPE_FILTERS.map(({ value, label }) => (
              <button
                key={value}
                onClick={() => setTypeFilter(value)}
                className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                  typeFilter === value
                    ? "bg-blue-600 text-white"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {label}
              </button>
            ))}
          </div>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as "rate" | "amount")}
            className="text-sm border border-gray-200 rounded-lg px-2.5 py-1.5 outline-none text-gray-600"
          >
            <option value="rate">금리 낮은 순</option>
            <option value="amount">한도 높은 순</option>
          </select>
        </div>
      </div>

      {/* 결과 없음 */}
      {filtered.length === 0 && (
        <div className="text-center py-16 text-gray-400">
          <p className="text-4xl mb-3">🔍</p>
          <p className="font-semibold">해당 조건의 상품이 없어요</p>
          <p className="text-sm mt-1">필터를 변경하거나 다시 검색해보세요</p>
        </div>
      )}

      {/* 정책 카드 목록 */}
      <div className="flex flex-col gap-4">
        {filtered.map((policy, i) => (
          <PolicyCard key={policy.id} policy={policy} rank={i + 1} />
        ))}
      </div>

      {filtered.length > 0 && (
        <p className="text-center text-xs text-gray-400 mt-6 pb-8">
          * 실제 금리·조건은 기관별로 변동될 수 있습니다. 신청 전 반드시 공식 사이트를 확인하세요.
        </p>
      )}
    </div>
  );
}
