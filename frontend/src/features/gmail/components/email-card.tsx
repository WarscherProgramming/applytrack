import { format, parseISO } from 'date-fns';
import {
  ChevronDown,
  ChevronRight,
  Copy,
  ExternalLink,
  Paperclip,
} from 'lucide-react';
import { useState } from 'react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useToast } from '@/hooks/use-toast';

import type { EmailMessage } from '../types';

/** Deep link to the message in the Gmail web UI (by Gmail message id). */
function gmailUrl(messageId: string): string {
  return `https://mail.google.com/mail/u/0/#all/${messageId}`;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface EmailCardProps {
  email: EmailMessage;
  defaultExpanded?: boolean;
}

/** A single imported email: collapsible, with attachments and Gmail actions. */
export function EmailCard({ email, defaultExpanded = false }: EmailCardProps) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  const { toast } = useToast();

  const senderLabel = email.sender_name ?? email.sender;
  const url = gmailUrl(email.message_id);

  async function copyLink() {
    try {
      await navigator.clipboard.writeText(url);
      toast({ title: 'Gmail link copied' });
    } catch {
      toast({ variant: 'destructive', title: 'Could not copy link' });
    }
  }

  return (
    <div className="rounded-lg border bg-card">
      <button
        type="button"
        onClick={() => setExpanded((v) => !v)}
        className="flex w-full items-start gap-3 p-3 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
        aria-expanded={expanded}
      >
        <span className="mt-0.5 text-muted-foreground">
          {expanded ? (
            <ChevronDown className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className="truncate text-sm font-medium">{senderLabel}</span>
            <Badge variant={email.direction === 'outbound' ? 'secondary' : 'outline'}>
              {email.direction === 'outbound' ? 'Sent' : 'Inbox'}
            </Badge>
            {email.attachments.length > 0 ? (
              <Paperclip className="h-3.5 w-3.5 text-muted-foreground" />
            ) : null}
          </div>
          <p className="truncate text-sm">{email.subject ?? '(no subject)'}</p>
          {!expanded && email.body_preview ? (
            <p className="truncate text-xs text-muted-foreground">
              {email.body_preview}
            </p>
          ) : null}
        </div>
        <span className="shrink-0 text-xs text-muted-foreground">
          {format(parseISO(email.sent_at), 'MMM d, h:mm a')}
        </span>
      </button>

      {expanded ? (
        <div className="space-y-3 border-t px-3 pb-3 pt-2 pl-10">
          <p className="text-xs text-muted-foreground">
            From <span className="text-foreground">{email.sender}</span>
            {email.recipients.length > 0 ? (
              <> · To {email.recipients.join(', ')}</>
            ) : null}
          </p>
          {email.body_preview ? (
            <p className="text-sm text-muted-foreground">{email.body_preview}</p>
          ) : null}

          {email.attachments.length > 0 ? (
            <div className="space-y-1">
              {email.attachments.map((att) => (
                <div
                  key={att.filename}
                  className="flex items-center gap-2 rounded-md border bg-muted/40 px-2 py-1 text-xs"
                >
                  <Paperclip className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="truncate">{att.filename}</span>
                  <span className="ml-auto text-muted-foreground">
                    {formatSize(att.size)}
                  </span>
                </div>
              ))}
            </div>
          ) : null}

          <div className="flex flex-wrap items-center gap-2">
            {email.match_reason ? (
              <Badge variant="success" className={cn('font-normal')}>
                {email.match_reason} · {Math.round(email.match_confidence * 100)}%
              </Badge>
            ) : null}
            <div className="ml-auto flex gap-2">
              <Button size="sm" variant="outline" onClick={copyLink}>
                <Copy className="h-4 w-4" />
                Copy link
              </Button>
              <Button size="sm" variant="outline" asChild>
                <a href={url} target="_blank" rel="noreferrer noopener">
                  <ExternalLink className="h-4 w-4" />
                  Open in Gmail
                </a>
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  );
}
