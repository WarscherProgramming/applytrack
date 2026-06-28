import type { BaseEntity, PaginationParams } from '@/types/api';

export type TaskStatus =
  | 'backlog'
  | 'today'
  | 'in_progress'
  | 'completed'
  | 'dismissed';

export type TaskPriority = 'low' | 'medium' | 'high' | 'urgent';

export type TaskSource =
  | 'manual'
  | 'followup'
  | 'interview'
  | 'gmail'
  | 'opportunity'
  | 'ai_recommendation'
  | 'daily_briefing';

export interface Task extends BaseEntity {
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  due_date: string | null;
  completed_at: string | null;
  source: TaskSource;
  application_id: string | null;
  company_id: string | null;
  recruiter_id: string | null;
  interview_id: string | null;
  followup_id: string | null;
  opportunity_id: string | null;
  source_key: string | null;
}

export interface TaskListParams extends PaginationParams {
  status?: TaskStatus;
  priority?: TaskPriority;
  source?: TaskSource;
}

export interface TaskCreateInput {
  title: string;
  description?: string | null;
  status?: TaskStatus;
  priority?: TaskPriority;
  due_date?: string | null;
  source?: TaskSource;
}

export type TaskUpdateInput = Partial<TaskCreateInput>;

export interface TaskGenerationResponse {
  created: number;
  updated: number;
  skipped: number;
  items: Task[];
}
