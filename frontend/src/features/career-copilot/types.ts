export interface PipelineStage {
  status: string;
  count: number;
}

export interface TodayMetrics {
  active_applications: number;
  followups_due_today: number;
  overdue_followups: number;
  upcoming_interviews: number;
  recent_emails: number;
  response_rate: number | null;
  interview_rate: number | null;
}

export type CopilotPriority = 'urgent' | 'high' | 'medium' | 'low';

export interface PriorityItem {
  id: string;
  rank: number;
  title: string;
  detail: string;
  reason: string;
  priority: CopilotPriority;
  source: string;
  due_at: string | null;
}

export interface DeadlineItem {
  id: string;
  kind: string;
  title: string;
  subtitle: string | null;
  due_at: string;
  priority: CopilotPriority;
}

export interface TimelineItem {
  id: string;
  kind: string;
  title: string;
  subtitle: string | null;
  timestamp: string;
}

export interface GmailActivityItem {
  id: string;
  subject: string;
  sender: string;
  sent_at: string;
  direction: string;
  match_reason: string | null;
}

export interface UpcomingInterviewItem {
  id: string;
  application_id: string;
  title: string;
  interview_type: string | null;
  scheduled_at: string;
  location: string | null;
}

export interface SkillFocus {
  skill: string;
  count: number;
  percentage: number | null;
  reason: string;
}

export interface ResumeRecommendation {
  title: string;
  detail: string;
  evidence: string | null;
}

export interface Reminder {
  title: string;
  detail: string;
  due_date: string | null;
  severity: CopilotPriority;
}

export interface DailyBriefing {
  generated_at: string;
  executive_summary: string;
  top_priorities: PriorityItem[];
  upcoming_deadlines: DeadlineItem[];
  ai_recommendations: string[];
  skill_focus: SkillFocus[];
  resume_recommendation: ResumeRecommendation | null;
  interview_preparation_reminder: Reminder;
  follow_up_reminder: Reminder;
}

export interface CopilotNarrative {
  available: boolean;
  provider: string | null;
  model: string | null;
  executive_summary: string;
  ai_recommendations: string[];
  skill_focus: string;
  resume_recommendation: string;
  interview_preparation_reminder: string;
  follow_up_reminder: string;
  caveats: string[];
}

export interface CareerCopilotResponse {
  generated_at: string;
  briefing: DailyBriefing;
  today_metrics: TodayMetrics;
  application_pipeline: PipelineStage[];
  upcoming_timeline: TimelineItem[];
  recent_gmail_activity: GmailActivityItem[];
  upcoming_interviews: UpcomingInterviewItem[];
  deterministic_priorities: PriorityItem[];
  ai_insight_panel: CopilotNarrative;
}

