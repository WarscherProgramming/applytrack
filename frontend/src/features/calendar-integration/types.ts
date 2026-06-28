export type CalendarProvider = 'google' | 'outlook' | 'ics';
export type CalendarConnectionStatus = 'connected' | 'disconnected' | 'error';

export interface CalendarConnection {
  provider: CalendarProvider;
  status: CalendarConnectionStatus;
  account_email: string | null;
  calendar_id: string | null;
  last_sync_at: string | null;
  last_sync_status: string | null;
  last_error: string | null;
}

export interface CalendarStatusResponse {
  connections: CalendarConnection[];
  synced_event_count: number;
  last_sync_at: string | null;
  last_sync_status: string | null;
  last_error: string | null;
}

export interface CalendarConnectResponse {
  provider: CalendarProvider;
  authorization_url: string | null;
  connected: boolean;
  message: string;
}

export interface CalendarSyncSummary {
  provider: CalendarProvider;
  created: number;
  updated: number;
  skipped: number;
  deleted: number;
  errors: string[];
  synced_event_count: number;
  last_sync_at: string;
}

export interface ManualSyncInput {
  provider: CalendarProvider;
  include_interviews?: boolean;
  include_followups?: boolean;
}
