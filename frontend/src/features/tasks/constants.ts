import type { TaskPriority, TaskSource, TaskStatus } from './types';

export const TASK_STATUSES: TaskStatus[] = [
  'backlog',
  'today',
  'in_progress',
  'completed',
  'dismissed',
];

export const TASK_PRIORITIES: TaskPriority[] = ['low', 'medium', 'high', 'urgent'];

export const TASK_SOURCES: TaskSource[] = [
  'manual',
  'followup',
  'interview',
  'gmail',
  'opportunity',
  'ai_recommendation',
  'daily_briefing',
];

export const TASK_VIEWS: TaskStatus[] = [
  'today',
  'backlog',
  'in_progress',
  'completed',
];
