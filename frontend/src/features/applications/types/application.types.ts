import type { BaseEntity, PaginationParams } from '@/types/api';

export type ApplicationStatus =
  | 'draft'
  | 'applied'
  | 'assessment'
  | 'phone_screen'
  | 'interview'
  | 'final_interview'
  | 'offer'
  | 'accepted'
  | 'rejected'
  | 'withdrawn'
  | 'ghosted';

export interface Application extends BaseEntity {
  company_id: string;
  job_title: string;
  job_link: string | null;
  location: string | null;
  salary_range: string | null;
  status: ApplicationStatus;
  date_applied: string | null;
  source: string | null;
  notes: string | null;
}

export interface ApplicationListParams extends PaginationParams {
  query?: string;
  status?: ApplicationStatus;
  company_id?: string;
}
