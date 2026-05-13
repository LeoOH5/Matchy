import { NextRequest, NextResponse } from "next/server";
import { getSupabase } from "@/lib/supabase";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const query = searchParams.get("query") ?? "";
  const type = searchParams.get("type");

  let q = getSupabase().from("policies").select("*").eq("is_active", true);

  if (type) q = q.eq("policy_type", type);
  if (query) {
    q = q.or(`name.ilike.%${query}%,tags.cs.["${query}"]`);
  }

  q = q.order("loan_rate_min", { ascending: true, nullsFirst: false });

  const { data, error } = await q;
  if (error) return NextResponse.json({ error: error.message }, { status: 500 });

  return NextResponse.json({ count: data?.length ?? 0, policies: data ?? [] });
}
