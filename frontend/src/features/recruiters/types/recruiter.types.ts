import type { BaseEntity, PaginationParams } from '@/types/api';

export interface Recruiter extends BaseEntity {
  company_id: string | null;
  first_name: string | null;
  last_name: string | null;
  email: string | null;
  phone: string | null;
  title: string | null;
  linkedin_url: string | null;
  notes: string | null;
}

export interface RecruiterCreateInput {
  company_id?: string | null;
  first_name?: string | null;
  last_name?: string | null;
  email?: string | null;
  phone?: string | null;
  title?: string | null;
  linkedin_url?: string | null;
  notes?: string | null;
}

/** Partial update — only provided fields are written (PATCH semantics). */
export type RecruiterUpdateInput = Partial<RecruiterCreateInput>;

export interface RecruiterListParams extends PaginationParams {
  /** Case-insensitive substring match on name, email, or title. */
  query?: string;
  company_id?: string;
}
