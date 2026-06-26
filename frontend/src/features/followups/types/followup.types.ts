import type { BaseEntity, PaginationParams } from '@/types/api';

export type FollowUpStatus = 'pending' | 'completed' | 'skipped';

export type FollowUpPriority = 'low' | 'medium' | 'high' | 'urgent';

export type FollowUpType =
  | 'email'
  | 'phone_call'
  | 'linkedin'
  | 'thank_you'
  | 'recruiter_checkin'
  | 'interview_followup'
  | 'application_checkin'
  | 'custom';

export interface FollowUp extends BaseEntity {
  application_id: string;
  recruiter_id: string | null;
  interview_id: string | null;
  title: string;
  description: string | null;
  followup_type: FollowUpType;
  status: FollowUpStatus;
  priority: FollowUpPriority;
  due_date: string;
  completed_at: string | null;
}

export interface FollowUpListParams extends PaginationParams {
  application_id?: string;
  recruiter_id?: string;
  interview_id?: string;
  status?: FollowUpStatus;
  priority?: FollowUpPriority;
  followup_type?: FollowUpType;
}
