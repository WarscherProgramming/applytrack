import type { AuthUser } from '@/features/auth/types';
import type { BaseEntity } from '@/types/api';

export type ThemePreference = 'light' | 'dark' | 'system';
export type DashboardPagePreference =
  | 'career_copilot'
  | 'dashboard'
  | 'career_intelligence'
  | 'daily_briefing'
  | 'tasks';
export type NotificationBehavior = 'all' | 'important_only' | 'muted';
export type CalendarProviderPreference = 'none' | 'ics' | 'google' | 'outlook';
export type AiProviderPreference = 'auto' | 'mock' | 'openai';

export interface NotificationPreferences {
  follow_up_reminders: boolean;
  interview_reminders: boolean;
  gmail_activity: boolean;
  opportunity_alerts: boolean;
  ai_insight_alerts: boolean;
}

export interface UserSettings extends BaseEntity {
  user_id: string;
  timezone: string;
  notification_preferences: NotificationPreferences;
  theme: ThemePreference;
  default_dashboard_page: DashboardPagePreference;
  default_notification_behavior: NotificationBehavior;
  preferred_calendar_provider: CalendarProviderPreference;
  preferred_ai_provider: AiProviderPreference;
}

export interface SettingsCenter {
  account: AuthUser;
  settings: UserSettings;
  available_ai_providers: string[];
}

export interface AccountSettingsInput {
  full_name?: string | null;
  email?: string;
  timezone?: string;
  notification_preferences?: NotificationPreferences;
}

export interface PreferencesInput {
  theme?: ThemePreference;
  default_dashboard_page?: DashboardPagePreference;
  default_notification_behavior?: NotificationBehavior;
  preferred_calendar_provider?: CalendarProviderPreference;
  preferred_ai_provider?: AiProviderPreference;
}

export interface NotificationSettingsInput {
  notification_preferences?: NotificationPreferences;
  default_notification_behavior?: NotificationBehavior;
}

export interface PasswordChangeInput {
  current_password: string;
  new_password: string;
  current_refresh_token?: string;
}

export interface PasswordChangeResponse {
  password_changed: boolean;
  old_refresh_tokens_invalidated: boolean;
}

export interface SessionInfo {
  id: string;
  created_at: string;
  expires_at: string;
  revoked_at: string | null;
  is_current: boolean;
  is_active: boolean;
}

export interface SessionListResponse {
  items: SessionInfo[];
  active_count: number;
}

export interface SessionActionResponse {
  signed_out: boolean;
  revoked_count: number;
}

export interface DataExportResponse {
  exported_at: string;
  user: AuthUser;
  data: Record<string, Array<Record<string, unknown>>>;
}
