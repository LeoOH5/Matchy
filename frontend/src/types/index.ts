export interface UserProfile {
  name: string;
  birth_year: number;
  gender: "male" | "female";
  income: number;           // 연소득 (만원)
  region: string;
  employment_status: "employed" | "unemployed" | "student" | "freelance";
  employment_type: "sme" | "large" | "public" | null;
  housing_type: "jeonse" | "monthly" | "own" | "parents";
  marital_status: "single" | "married" | "newlywed";
  purpose: string[];
  household_members: number;
  assets: number | null;
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
  is_active: number;
}

export interface MatchResult {
  age: number;
  matched_count: number;
  policies: Policy[];
}
