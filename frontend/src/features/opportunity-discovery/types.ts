import type { Application } from '@/features/applications/types/application.types';

export type JobProviderName = 'greenhouse' | 'lever' | 'ashby' | 'rss';
export type WorkMode = 'remote' | 'hybrid' | 'onsite' | 'unknown';

export interface SkillTag {
  name: string;
  category: string;
}

export interface NormalizedJobPosting {
  id: string;
  provider: JobProviderName;
  provider_job_id: string | null;
  company: string;
  title: string;
  location: string | null;
  salary: string | null;
  employment_type: string | null;
  work_mode: WorkMode;
  job_url: string;
  posted_at: string | null;
  description: string;
  skills: SkillTag[];
  industry: string | null;
}

export interface OpportunitySearchRequest {
  query?: string | null;
  providers?: JobProviderName[];
  greenhouse_boards?: string[];
  lever_companies?: string[];
  ashby_boards?: string[];
  rss_feeds?: string[];
  remote?: WorkMode | null;
  location?: string | null;
  min_salary?: number | null;
  technologies?: string[];
  resume_id?: string | null;
  preferred_location?: string | null;
  preferred_job_type?: string | null;
  preferred_industry?: string | null;
  limit?: number;
}

export interface ProviderIssue {
  provider: JobProviderName;
  source: string;
  message: string;
}

export interface OpportunityScore {
  overall_match_percent: number;
  resume_match_score: number | null;
  skill_overlap_percent: number | null;
  historical_response_rate: number | null;
  location_score: number | null;
  job_type_score: number | null;
  industry_score: number | null;
  reasoning: string[];
  top_missing_skills: string[];
  matched_skills: string[];
  recommended_resume_id: string | null;
  recommended_resume_name: string | null;
  suggested_cover_letter_id: string | null;
  suggested_cover_letter_name: string | null;
}

export interface OpportunityAIExplanation {
  available: boolean;
  provider: string | null;
  model: string | null;
  summary: string;
  score_explanation: string;
  next_steps: string[];
  cautions: string[];
}

export interface ScoredOpportunity {
  posting: NormalizedJobPosting;
  score: OpportunityScore;
  ai_explanation: OpportunityAIExplanation;
}

export interface SkillTagSummary {
  name: string;
  category: string;
  count: number;
}

export interface DistributionSummary {
  name: string;
  count: number;
}

export interface OpportunitySearchResponse {
  items: ScoredOpportunity[];
  total: number;
  provider_issues: ProviderIssue[];
  top_technologies: SkillTagSummary[];
  top_industries: DistributionSummary[];
  top_locations: DistributionSummary[];
}

export interface SaveOpportunityRequest {
  posting: NormalizedJobPosting;
  resume_id?: string | null;
  cover_letter_id?: string | null;
}

export interface SaveOpportunityResponse {
  application: Application;
  company_created: boolean;
}
