/** Token/cost/latency summary returned with each generation. */
export interface UsageSummary {
  provider: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  estimated_cost_usd: number | null;
  latency_ms: number;
}

export interface CoverLetterGenerateInput {
  resume_id: string;
  job_description: string;
  application_id?: string | null;
  company_name?: string | null;
  job_title?: string | null;
  template_cover_letter_id?: string | null;
  user_notes?: string | null;
}

export interface CoverLetterGenerateResponse {
  markdown: string;
  plain_text: string;
  resume_name: string;
  company_name: string;
  job_title: string;
  usage: UsageSummary;
}

export interface CoverLetterSaveInput {
  name: string;
  content: string;
  notes?: string | null;
}

/** A saved cover letter version (mirrors the library DocumentResponse). */
export interface SavedCoverLetter {
  id: string;
  name: string;
  file_name: string;
  version: number;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

export interface CoverLetterVersionContent {
  id: string;
  name: string;
  version: number;
  file_name: string;
  created_at: string;
  content: string;
}

/** A generation kept in the page session for the "generation history" panel. */
export interface GenerationHistoryEntry {
  id: string;
  createdAt: number;
  company_name: string;
  job_title: string;
  resume_name: string;
  markdown: string;
  plain_text: string;
  usage: UsageSummary;
}
