export interface JobIntelligenceParams {
  date_from?: string;
  date_to?: string;
  industry?: string;
  company?: string;
  role?: string;
}

export interface DistributionItem {
  name: string;
  count: number;
  percentage: number | null;
}

export interface TrendPoint {
  period: string;
  count: number;
}

export interface SkillSignal {
  name: string;
  category: string;
  frequency: number;
  percentage: number | null;
  trend_delta: number;
  trend: TrendPoint[];
  industry_distribution: DistributionItem[];
  company_distribution: DistributionItem[];
  role_distribution: DistributionItem[];
}

export interface CategoryBreakdown {
  category: string;
  count: number;
  skills: SkillSignal[];
}

export interface MissingSkill {
  name: string;
  category: string;
  market_frequency: number;
  market_percentage: number | null;
  resume_match_gap_count: number;
  reason: string;
}

export interface JobIntelligenceAI {
  available: boolean;
  provider: string | null;
  model: string | null;
  executive_summary: string;
  top_learning_priorities: string[];
  emerging_technologies: string[];
  resume_recommendations: string[];
  skill_investment_suggestions: string[];
  career_direction_suggestions: string[];
  caveats: string[];
}

export interface JobIntelligenceResponse {
  generated_at: string;
  job_description_count: number;
  source_count: number;
  resume_skill_count: number;
  skill_signals: SkillSignal[];
  category_breakdown: CategoryBreakdown[];
  missing_skills: MissingSkill[];
  industry_breakdown: DistributionItem[];
  company_breakdown: DistributionItem[];
  role_breakdown: DistributionItem[];
  ai_interpretation: JobIntelligenceAI;
}

