export type NotificationPriority = 'low' | 'medium' | 'high' | 'urgent';
export type NotificationCategory =
  | 'follow_up'
  | 'interview'
  | 'gmail'
  | 'opportunity'
  | 'ai_insight';

export interface BriefingItem {
  id: string;
  title: string;
  detail: string;
  priority: NotificationPriority;
  category: NotificationCategory | null;
  due_at: string | null;
  action_url: string | null;
}

export interface RecruiterEmailItem {
  id: string;
  subject: string;
  sender: string;
  sent_at: string;
  match_reason: string | null;
}

export interface OpportunityHighlight {
  id: string;
  company: string;
  title: string;
  created_at: string;
  source: string | null;
  job_url: string | null;
}

export interface ResumePerformanceChange {
  title: string;
  detail: string;
  evidence: string | null;
}

export interface SkillTrendUpdate {
  skill: string;
  category: string;
  frequency: number;
  trend_delta: number;
  percentage: number | null;
}

export interface DailyBriefingAI {
  available: boolean;
  provider: string | null;
  model: string | null;
  morning_summary: string;
  recommendations: string[];
  caveats: string[];
}

export interface NotificationItem {
  id: string;
  created_at: string;
  updated_at: string;
  title: string;
  message: string;
  category: NotificationCategory;
  priority: NotificationPriority;
  source_type: string | null;
  source_id: string | null;
  action_url: string | null;
  dedupe_key: string;
  is_read: boolean;
  is_pinned: boolean;
  is_dismissed: boolean;
}

export interface NotificationListResponse {
  items: NotificationItem[];
  total: number;
  unread_count: number;
  pinned_count: number;
}

export interface NotificationUpdate {
  is_read?: boolean;
  is_pinned?: boolean;
  is_dismissed?: boolean;
}

export interface DailyBriefingResponse {
  generated_at: string;
  briefing_date: string;
  morning_summary: string;
  followups_due_today: BriefingItem[];
  overdue_followups: BriefingItem[];
  upcoming_interviews: BriefingItem[];
  new_recruiter_emails: RecruiterEmailItem[];
  newly_discovered_opportunities: OpportunityHighlight[];
  resume_performance_changes: ResumePerformanceChange[];
  skill_trend_updates: SkillTrendUpdate[];
  ai_recommendations: string[];
  prioritized_actions: BriefingItem[];
  pinned_notifications: NotificationItem[];
  unread_notification_count: number;
  ai_narrative: DailyBriefingAI;
}
