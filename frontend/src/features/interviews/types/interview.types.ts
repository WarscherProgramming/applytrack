import type { BaseEntity, PaginationParams } from '@/types/api';

export type InterviewStatus =
  | 'scheduled'
  | 'completed'
  | 'cancelled'
  | 'rescheduled'
  | 'no_show';

export type InterviewType =
  | 'phone_screen'
  | 'technical'
  | 'behavioral'
  | 'onsite'
  | 'final'
  | 'recruiter_call'
  | 'hiring_manager'
  | 'other';

export interface Interview extends BaseEntity {
  application_id: string;
  recruiter_id: string | null;
  interview_type: InterviewType | null;
  scheduled_at: string;
  duration_minutes: number;
  location: string | null;
  meeting_link: string | null;
  status: InterviewStatus;
  notes: string | null;
  feedback: string | null;
}

export interface InterviewListParams extends PaginationParams {
  application_id?: string;
  recruiter_id?: string;
  status?: InterviewStatus;
  interview_type?: InterviewType;
}
