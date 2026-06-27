import type { BaseEntity, PaginationParams } from '@/types/api';

export interface CompanyOverview {
  mission: string;
  products_services: string[];
  industry: string;
  culture: string;
  recent_news: string;
}

export interface LikelyQuestions {
  behavioral: string[];
  technical: string[];
  role_specific: string[];
  company_specific: string[];
}

export interface StarExample {
  question: string;
  situation: string;
  task: string;
  action: string;
  result: string;
}

export interface StudyTopics {
  languages: string[];
  frameworks: string[];
  concepts: string[];
  system_design: string[];
  algorithms: string[];
  role_specific: string[];
}

export interface RedFlags {
  missing_resume_coverage: string[];
  skill_gaps: string[];
  likely_challenges: string[];
}

export interface InterviewPrepResult {
  company_overview: CompanyOverview;
  likely_questions: LikelyQuestions;
  star_examples: StarExample[];
  study_topics: StudyTopics;
  questions_to_ask: string[];
  red_flags: RedFlags;
  checklist: string[];
}

export interface UsageSummary {
  provider: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number | null;
  latency_ms: number;
}

export interface InterviewPrepPackage extends BaseEntity {
  application_id: string | null;
  resume_id: string | null;
  company_name: string;
  job_title: string;
  interview_type: string | null;
  interview_round: string | null;
  job_description: string;
  result: InterviewPrepResult;
  usage: UsageSummary;
}

export interface InterviewPrepListItem extends BaseEntity {
  application_id: string | null;
  company_name: string;
  job_title: string;
  interview_type: string | null;
  interview_round: string | null;
  provider: string;
  model: string;
}

export interface InterviewPrepRequest {
  application_id?: string | null;
  resume_id?: string | null;
  company_name?: string | null;
  job_title?: string | null;
  job_description: string;
  interview_type?: string | null;
  interview_round?: string | null;
  recruiter_notes?: string | null;
  interview_notes?: string | null;
}

export interface InterviewPrepListParams extends PaginationParams {
  application_id?: string;
}
