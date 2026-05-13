"use client";
import { useState } from "react";
import { UserProfile, MatchResult } from "@/types";
import ProfileForm from "@/components/ProfileForm";
import ResultsView from "@/components/ResultsView";
import { matchPolicies } from "@/lib/api";

type Phase = "landing" | "form" | "results";

export default function Home() {
  const [phase, setPhase] = useState<Phase>("landing");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<MatchResult | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (p: UserProfile) => {
    setLoading(true);
    setError(null);
    try {
      const res = await matchPolicies(p);
      setProfile(p);
      setResult(res);
      setPhase("results");
    } catch {
      setError("서버에 연결할 수 없어요. API 서버가 실행 중인지 확인해주세요.");
    } finally {
      setLoading(false);
    }
  };

  const reset = () => {
    setPhase("landing");
    setResult(null);
    setProfile(null);
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* 네비게이션 */}
      <nav className="bg-white border-b border-gray-100 px-6 py-4 flex items-center gap-3 sticky top-0 z-10">
        <button onClick={reset} className="flex items-center gap-2 hover:opacity-80 transition-opacity">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">M</span>
          </div>
          <span className="font-bold text-gray-800 text-lg">Matchy</span>
        </button>
        <span className="text-gray-300">|</span>
        <span className="text-sm text-gray-500">청년 맞춤 정책 찾기</span>
      </nav>

      <main className={`flex-1 ${phase === "form" ? "" : "px-4 py-8"}`}>
        {/* 랜딩 */}
        {phase === "landing" && (
          <div className="max-w-2xl mx-auto text-center py-16">
            <div className="inline-flex items-center gap-2 bg-blue-50 text-blue-600 text-sm font-medium px-4 py-2 rounded-full mb-6">
              🎯 청년 맞춤 정책 매칭 서비스
            </div>
            <h1 className="text-4xl font-extrabold text-gray-900 mb-4 leading-tight">
              내게 딱 맞는<br />
              <span className="text-blue-600">청년 정책·대출</span>을 찾아드려요
            </h1>
            <p className="text-gray-500 text-lg mb-10 leading-relaxed">
              정부 지원금부터 주거 대출, 시중은행 상품까지<br />
              내 조건에 맞는 상품을 금리 낮은 순으로 보여드려요
            </p>

            {/* 특징 카드 */}
            <div className="grid grid-cols-3 gap-4 mb-10 text-left">
              {[
                { icon: "🏛", title: "정부 정책", desc: "청년정책포털·주택도시기금" },
                { icon: "🏦", title: "시중은행", desc: "KB·신한·우리·카카오뱅크" },
                { icon: "⚡", title: "즉시 매칭", desc: "조건 입력 후 바로 확인" },
              ].map(({ icon, title, desc }) => (
                <div key={title} className="bg-white rounded-2xl p-4 border border-gray-100 shadow-sm">
                  <div className="text-2xl mb-2">{icon}</div>
                  <p className="font-semibold text-gray-700 text-sm">{title}</p>
                  <p className="text-gray-400 text-xs mt-1">{desc}</p>
                </div>
              ))}
            </div>

            <button
              onClick={() => setPhase("form")}
              className="bg-blue-600 hover:bg-blue-700 text-white font-bold px-10 py-4 rounded-2xl text-lg transition-colors shadow-lg shadow-blue-200"
            >
              내 조건으로 정책 찾기 →
            </button>
            <p className="text-xs text-gray-400 mt-4">회원가입 없이 바로 사용 가능</p>
          </div>
        )}

        {/* 폼 */}
        {phase === "form" && (
          <div className="max-w-lg mx-auto">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-600 rounded-xl p-4 mx-4 mt-4 text-sm">
                ⚠️ {error}
              </div>
            )}
            <ProfileForm onSubmit={handleSubmit} loading={loading} />
          </div>
        )}

        {/* 결과 */}
        {phase === "results" && result && profile && (
          <ResultsView result={result} profile={profile} onReset={reset} />
        )}
      </main>

      <footer className="text-center text-xs text-gray-400 py-6 border-t border-gray-100">
        © 2026 Matchy · 실제 금리·조건은 기관별로 변동될 수 있습니다
      </footer>
    </div>
  );
}
