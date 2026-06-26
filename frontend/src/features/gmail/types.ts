import type { BaseEntity } from '@/types/api';

export interface EmailAttachment {
  filename: string;
  mime_type: string | null;
  size: number;
}

export interface EmailMessage extends BaseEntity {
  message_id: string;
  thread_id: string;
  subject: string | null;
  sender: string;
  sender_name: string | null;
  recipients: string[];
  sent_at: string;
  body_preview: string | null;
  direction: 'inbound' | 'outbound';
  labels: string[];
  attachments: EmailAttachment[];
  company_id: string | null;
  application_id: string | null;
  recruiter_id: string | null;
  interview_id: string | null;
  match_confidence: number;
  match_reason: string | null;
}

export interface GmailStatus {
  connected: boolean;
  email_address: string | null;
  last_sync_at: string | null;
  last_sync_status: string | null;
  email_count: number;
  simulation: boolean;
}

export interface GmailConnectResponse {
  connected: boolean;
  authorization_url: string | null;
  message: string;
}

export interface GmailSyncResponse {
  imported: number;
  updated: number;
  matched: number;
  total_processed: number;
  last_sync_at: string;
}

/** Filters for the email list — also the props an EmailTimeline scopes to. */
export interface EmailListParams {
  application_id?: string;
  company_id?: string;
  recruiter_id?: string;
  interview_id?: string;
  query?: string;
  skip?: number;
  limit?: number;
}

export interface EmailListResponse {
  items: EmailMessage[];
  total: number;
  skip: number;
  limit: number;
}

export interface TimelineEvent {
  id: string;
  kind: 'application' | 'recruiter' | 'interview' | 'email' | 'offer' | 'rejection';
  title: string;
  subtitle: string | null;
  timestamp: string;
}
