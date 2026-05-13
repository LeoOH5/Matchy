import { createClient, SupabaseClient } from "@supabase/supabase-js";

let _client: SupabaseClient | null = null;

export function getSupabase(): SupabaseClient {
  if (!_client) {
    const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
    const key = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;
    _client = createClient(url, key);
  }
  return _client;
}

export interface Policy {
  id: string;
  name: string;
  source: string;
  source_url: string | null;
  policy_type: string;
  description: string | null;
  age_min: number | null;
  age_max: number | null;
  income_max: number | null;
  income_desc: string | null;
  regions: string[];
  loan_rate_min: number | null;
  loan_rate_max: number | null;
  loan_amount_max: number | null;
  loan_period_max: number | null;
  loan_collateral: string | null;
  grant_amount: number | null;
  application_url: string | null;
  tags: string[];
  is_active: boolean;
}
