import { UserProfile, MatchResult } from "@/types";

export async function matchPolicies(profile: UserProfile): Promise<MatchResult> {
  const res = await fetch("/api/match", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });
  if (!res.ok) throw new Error("매칭 요청 실패");
  return res.json();
}
