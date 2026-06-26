import type { BaseEntity, PaginationParams } from '@/types/api';

export interface Company extends BaseEntity {
  name: string;
  website: string | null;
  industry: string | null;
  location: string | null;
  notes: string | null;
}

export interface CompanyCreateInput {
  name: string;
  website?: string | null;
  industry?: string | null;
  location?: string | null;
  notes?: string | null;
}

/** Partial update — only provided fields are written (PATCH semantics). */
export type CompanyUpdateInput = Partial<CompanyCreateInput>;

export interface CompanyListParams extends PaginationParams {
  /** Case-insensitive substring match on the company name. */
  query?: string;
}
