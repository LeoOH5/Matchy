import { Policy } from "@/types";

const TYPE_BADGE: Record<string, { label: string; color: string }> = {
  주거대출: { label: "주거대출", color: "bg-blue-100 text-blue-700" },
  정부대출: { label: "정부대출", color: "bg-green-100 text-green-700" },
  은행대출: { label: "은행대출", color: "bg-purple-100 text-purple-700" },
  지원금: { label: "지원금", color: "bg-orange-100 text-orange-700" },
  취업: { label: "취업지원", color: "bg-teal-100 text-teal-700" },
  교육: { label: "교육지원", color: "bg-pink-100 text-pink-700" },
  기타: { label: "기타", color: "bg-gray-100 text-gray-600" },
};

const SOURCE_ICON: Record<string, string> = {
  주택도시기금: "🏛",
  KB국민은행: "🏦",
  신한은행: "🏦",
  우리은행: "🏦",
  IBK기업은행: "🏦",
  카카오뱅크: "📱",
  청년정책포털: "📋",
};

interface Props {
  policy: Policy;
  rank?: number;
}

export default function PolicyCard({ policy, rank }: Props) {
  const badge = TYPE_BADGE[policy.policy_type] ?? TYPE_BADGE["기타"];
  const icon = SOURCE_ICON[policy.source] ?? "📄";

  const rateText = policy.loan_rate_min != null
    ? policy.loan_rate_min === policy.loan_rate_max
      ? `연 ${policy.loan_rate_min}%`
      : `연 ${policy.loan_rate_min}% ~ ${policy.loan_rate_max}%`
    : null;

  const amountText = policy.loan_amount_max != null
    ? policy.loan_amount_max >= 10000
      ? `최대 ${(policy.loan_amount_max / 10000).toFixed(1)}억원`
      : `최대 ${policy.loan_amount_max.toLocaleString()}만원`
    : null;

  const periodText = policy.loan_period_max != null
    ? policy.loan_period_max % 12 === 0
      ? `최대 ${policy.loan_period_max / 12}년`
      : `최대 ${policy.loan_period_max}개월`
    : null;

  const ageText = policy.age_min != null || policy.age_max != null
    ? `만 ${policy.age_min ?? ""}~${policy.age_max ?? ""}세`
    : null;

  return (
    <div className="bg-white rounded-2xl border border-gray-100 shadow-sm hover:shadow-md transition-shadow p-5 flex flex-col gap-4">
      {/* 헤더 */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-3">
          {rank != null && (
            <span className="shrink-0 w-7 h-7 rounded-full bg-blue-600 text-white text-xs font-bold flex items-center justify-center mt-0.5">
              {rank}
            </span>
          )}
          <div>
            <p className="text-xs text-gray-400 mb-0.5">{icon} {policy.source}</p>
            <h3 className="font-bold text-gray-800 leading-tight">{policy.name}</h3>
          </div>
        </div>
        <span className={`shrink-0 text-xs font-semibold px-2.5 py-1 rounded-full ${badge.color}`}>
          {badge.label}
        </span>
      </div>

      {/* 설명 */}
      {policy.description && (
        <p className="text-sm text-gray-500 leading-relaxed line-clamp-2">{policy.description}</p>
      )}

      {/* 핵심 조건 그리드 */}
      <div className="grid grid-cols-2 gap-2">
        {rateText && (
          <Stat icon="📊" label="금리" value={rateText} highlight />
        )}
        {amountText && (
          <Stat icon="💰" label="한도" value={amountText} />
        )}
        {periodText && (
          <Stat icon="📅" label="기간" value={periodText} />
        )}
        {ageText && (
          <Stat icon="👤" label="대상 나이" value={ageText} />
        )}
        {policy.income_max && (
          <Stat icon="📋" label="소득 조건" value={`${policy.income_max.toLocaleString()}만원 이하`} />
        )}
        {policy.loan_collateral && (
          <Stat icon="🔒" label="담보" value={policy.loan_collateral} />
        )}
      </div>

      {/* 지역 태그 */}
      {policy.regions.length > 0 && (
        <div className="flex gap-1 flex-wrap">
          {policy.regions.map((r) => (
            <span key={r} className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded-full">{r}</span>
          ))}
        </div>
      )}

      {/* 신청 버튼 */}
      {policy.application_url && (
        <a
          href={policy.application_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-auto block text-center py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold transition-colors"
        >
          신청하러 가기 →
        </a>
      )}
    </div>
  );
}

function Stat({ icon, label, value, highlight }: {
  icon: string; label: string; value: string; highlight?: boolean;
}) {
  return (
    <div className={`rounded-xl p-2.5 ${highlight ? "bg-blue-50" : "bg-gray-50"}`}>
      <p className="text-xs text-gray-400 mb-0.5">{icon} {label}</p>
      <p className={`text-sm font-bold ${highlight ? "text-blue-700" : "text-gray-700"}`}>{value}</p>
    </div>
  );
}
