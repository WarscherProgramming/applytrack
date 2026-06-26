import { Mail } from 'lucide-react';
import { useMemo, useState } from 'react';

import { EmptyState } from '@/components/common/empty-state';
import { ErrorState } from '@/components/common/error-state';
import { LoadingSpinner } from '@/components/common/loading-spinner';
import { SearchBar } from '@/components/common/search-bar';
import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

import { useEmails } from '../hooks/use-gmail';
import type { EmailMessage } from '../types';
import { EmailCard } from './email-card';

interface EmailTimelineProps {
  /** Scope to a single entity. Omit all for a global timeline. */
  applicationId?: string;
  companyId?: string;
  recruiterId?: string;
  interviewId?: string;
  title?: string;
  description?: string;
  showSearch?: boolean;
}

interface Thread {
  id: string;
  subject: string | null;
  messages: EmailMessage[];
  latest: string;
}

/**
 * Reusable, self-contained email timeline. Pass an entity id to scope it (drops
 * straight into an Application/Company/Recruiter detail view) or omit ids for a
 * global view. Emails are grouped into conversation threads.
 */
export function EmailTimeline({
  applicationId,
  companyId,
  recruiterId,
  interviewId,
  title = 'Email timeline',
  description = 'Imported emails, grouped by conversation.',
  showSearch = true,
}: EmailTimelineProps) {
  const [query, setQuery] = useState('');

  const { data, isLoading, isError, error, refetch } = useEmails({
    application_id: applicationId,
    company_id: companyId,
    recruiter_id: recruiterId,
    interview_id: interviewId,
    query: query || undefined,
    limit: 100,
  });

  const threads = useMemo<Thread[]>(() => {
    const map = new Map<string, EmailMessage[]>();
    for (const email of data?.items ?? []) {
      const list = map.get(email.thread_id);
      if (list) list.push(email);
      else map.set(email.thread_id, [email]);
    }
    return [...map.values()]
      .map((messages) => {
        const sorted = [...messages].sort((a, b) =>
          a.sent_at.localeCompare(b.sent_at),
        );
        return {
          id: sorted[0].thread_id,
          subject: sorted[0].subject,
          messages: sorted,
          latest: sorted[sorted.length - 1].sent_at,
        };
      })
      .sort((a, b) => b.latest.localeCompare(a.latest));
  }, [data]);

  const isEmpty = !isLoading && threads.length === 0;

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <CardTitle>{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
          {showSearch ? (
            <SearchBar
              value={query}
              onChange={setQuery}
              placeholder="Search emails…"
            />
          ) : null}
        </div>
      </CardHeader>

      <CardContent>
        {isError ? (
          <ErrorState error={error} onRetry={refetch} className="py-8" />
        ) : isLoading ? (
          <LoadingSpinner label="Loading emails…" />
        ) : isEmpty ? (
          <EmptyState
            icon={Mail}
            title={query ? 'No emails match your search' : 'No emails imported'}
            description={
              query
                ? 'Try a different search term.'
                : 'Connect Gmail and run a sync to import job-related emails.'
            }
            className="border-0 py-8"
          />
        ) : (
          <div className="space-y-4">
            {threads.map((thread) => (
              <div key={thread.id} className="space-y-2">
                {thread.messages.length > 1 ? (
                  <div className="flex items-center gap-2 px-1">
                    <h4 className="truncate text-sm font-medium">
                      {thread.subject ?? '(no subject)'}
                    </h4>
                    <Badge variant="secondary">
                      {thread.messages.length} messages
                    </Badge>
                  </div>
                ) : null}
                <div className="space-y-2">
                  {thread.messages.map((email) => (
                    <EmailCard key={email.id} email={email} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
