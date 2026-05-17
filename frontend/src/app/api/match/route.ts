import { NextRequest, NextResponse } from "next/server";
import { getSupabase, Policy } from "@/lib/supabase";

interface UserProfile {
  name: string;
  birth_year: number;
  gender: string;
  income: number;
  region: string;
  employment_status: string;
  employment_type: string | null;
  housing_type: string;
  marital_status: string;
  purpose: string[];
  household_members: number;
  assets: number | null;
}

const KEYWORD_MAP: Record<string, string> = {
  전세대출: "전세",
  월세대출: "월세",
  원룸대출: "전세",
  주택구입: "구입",
  창업지원: "창업",
  취업지원: "취업",
  교육비: "교육",
  주거지원: "주거",
};

async function searchPolicies(opts: {
  query?: string;
  age?: number;
  income?: number;
  region?: string;
}): Promise<Policy[]> {
  let q = getSupabase()
    .from("policies")
    .select("*")
    .eq("is_active", true);

  if (opts.age !== undefined) {
    q = q
      .or(`age_min.is.null,age_min.lte.${opts.age}`)
      .or(`age_max.is.null,age_max.gte.${opts.age}`);
  }

  if (opts.income !== undefined) {
    q = q.or(`income_max.is.null,income_max.gte.${opts.income}`);
  }

  if (opts.region && opts.region !== "전국") {
    q = q.or(`regions.eq.[],regions.cs.["${opts.region}"]`);
  }

  if (opts.query) {
    q = q.or(
      `name.ilike.%${opts.query}%,description.ilike.%${opts.query}%,tags.cs.["${opts.query}"]`
    );
  }

  q = q.order("loan_rate_min", { ascending: true, nullsFirst: false });

  const { data, error } = await q;
  if (error) {
    console.error("Supabase query error:", error);
    return [];
  }
  return (data ?? []) as Policy[];
}

export async function POST(req: NextRequest) {
  try {
    const profile: UserProfile = await req.json();
    const age = 2026 - profile.birth_year + 1;

    const seen = new Set<string>();
    const results: Policy[] = [];

    const addUnique = (policies: Policy[]) => {
      for (const p of policies) {
        if (!seen.has(p.id)) {
          seen.add(p.id);
          results.push(p);
        }
      }
    };

    // 목적별 검색
    for (const purpose of profile.purpose) {
      const keyword = KEYWORD_MAP[purpose] ?? purpose;
      const policies = await searchPolicies({
        query: keyword,
        age,
        income: profile.income,
        region: profile.region,
      });
      addUnique(policies);
    }

    // 중소기업 재직자 추가
    if (profile.employment_type === "sme") {
      const policies = await searchPolicies({ query: "중소기업", age, income: profile.income });
      addUnique(policies);
    }

    // 신혼부부 추가
    if (profile.marital_status === "newlywed") {
      const policies = await searchPolicies({ query: "신혼", age });
      addUnique(policies);
    }

    // 결과 없으면 나이·소득 필터 없이 전체 재검색 (fallback)
    if (results.length === 0) {
      const fallback = await searchPolicies({});
      addUnique(fallback);
    }

    // 프로필 기반 사후 필터링
    const filtered = results.filter((p) => {
      const nameAndTags = p.name + " " + (p.tags ?? []).join(" ");

      // 신혼부부 전용 정책 → 신혼부부만
      if (/신혼/.test(nameAndTags) && profile.marital_status !== "newlywed") return false;

      // 중소기업 재직자 전용 정책 → 중소·중견기업 재직자만
      if (/중소기업/.test(nameAndTags) && profile.employment_type !== "sme") return false;

      // 재직자 대상 정책(청년내일채움공제 등) → 직장인만
      if (/내일채움|일자리도약장려금/.test(p.name) && profile.employment_status !== "employed") return false;

      // 학자금대출 → 학생만
      if (/학자금|국가장학금/.test(p.name) && profile.employment_status !== "student") return false;

      return true;
    });

    // 금리 낮은 순 → 한도 높은 순
    filtered.sort((a, b) => {
      const ra = a.loan_rate_min ?? 99;
      const rb = b.loan_rate_min ?? 99;
      if (ra !== rb) return ra - rb;
      return (b.loan_amount_max ?? 0) - (a.loan_amount_max ?? 0);
    });

    return NextResponse.json({ age, matched_count: filtered.length, policies: filtered });
  } catch (e) {
    console.error(e);
    return NextResponse.json({ error: "서버 오류가 발생했어요" }, { status: 500 });
  }
}
