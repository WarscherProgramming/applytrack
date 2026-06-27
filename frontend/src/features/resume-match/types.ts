import type { BaseEntity, PaginationParams } from '@/types/api';

/** The structured analysis the AI returns (mirrors backend ResumeMatchResult). */
export interface ResumeMatchResult {
  overall_match_score: number;
  strengths: string[];
  weaknesses: string[];
  missing_skills: string[];
  recommended_keywords: string[];
  recommended_resume_changes: string[];
  interview_topics: string[];
}

/** A full stored analysis (for display / reopening). */
export interface ResumeMatchAnalysis extends BaseEntity {
  resume_id: string | null;
  resume_name: string;
  job_description: string;
  overall_match_score: number;
  result: ResumeMatchResult;
  provider: string;
  model: string;
}

/** Lightweight history row returned by the list endpoint. */
export interface ResumeMatchListItem extends BaseEntity {
  resume_id: string | null;
  resume_name: string;
  overall_match_score: number;
  job_description_preview: string;
  provider: string;
  model: string;
}

export interface ResumeMatchRunInput {
  resume_id: string;
  job_description: string;
}

export interface ResumeMatchListParams extends PaginationParams {
  resume_id?: string;
}
