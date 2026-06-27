import {
  Bell,
  BellRing,
  CalendarClock,
  Download,
  Inbox,
  Mail,
  Pin,
  RefreshCw,
  Sparkles,
  X,
} from 'lucide-react';
import { Link } from 'react-router-dom';

import { EmptyState } from '@/components/common/empty-state';
import { ErrorState } from '@/components/common/error-state';
import { PageHeader } from '@/components/common/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  useDailyBriefing,
  useNotifications,
  useRefreshDailyBriefing,
  useUpdateNotification,
} from '@/features/daily-briefing/hooks';
import {
  downloadBriefing,
  priorityBadge,
  priorityLabel,
} from '@/features/daily-briefing/lib';
import type {
  BriefingItem,
  DailyBriefingResponse,
  NotificationItem,
} from '@/features/daily-briefing/types';
import { useToast } from '@/hooks/use-toast';

export function DailyBriefingPage() {
  const briefing = useDailyBriefing();
  const notifications = useNotifications();
  const refresh = useRefreshDailyBriefing();
  const updateNotification = useUpdateNotification();
  const { toast } = useToast();

  const data = briefing.data;

  const refreshBriefing = () => {
    refresh.mutate(undefined, {
      onSuccess: () => toast({ title: 'Briefing refreshed' }),
      onError: () => toast({ variant: 'destructive', title: 'Refresh failed' }),
    });
  };

  const update = (notification: NotificationItem, patch: Partial<NotificationItem>) => {
    updateNotification.mutate({
      id: notification.id,
      input: {
        is_read: patch.is_read,
        is_pinned: patch.is_pinned,
        is_dismissed: patch.is_dismissed,
      },
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Daily Briefing"
        description="A proactive briefing and notification center for today's job-search work."
        actions={
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={refreshBriefing}
              disabled={refresh.isPending}
            >
              <RefreshCw className={refresh.isPending ? 'h-4 w-4 animate-spin' : 'h-4 w-4'} />
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={!data}
              onClick={() => data && downloadBriefing(data)}
            >
              <Download className="h-4 w-4" />
              Export
            </Button>
          </>
        }
      />

      {briefing.isError ? (
        <ErrorState error={briefing.error} onRetry={() => briefing.refetch()} />
      ) : briefing.isLoading ? (
        <BriefingSkeleton />
      ) : data ? (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_380px]">
          <div className="space-y-4">
            <MorningBrief data={data} />
            <PriorityCards items={data.prioritized_actions} />
            <div className="grid gap-4 lg:grid-cols-2">
              <BriefingList
                title="Follow-ups"
                icon={Inbox}
                items={[...data.overdue_followups, ...data.followups_due_today]}
              />
              <BriefingList
                title="Upcoming interviews"
                icon={CalendarClock}
                items={data.upcoming_interviews}
              />
            </div>
            <OpportunityHighlights data={data} />
            <SkillAndResume data={data} />
          </div>

          <NotificationCenter
            items={notifications.data?.items ?? data.pinned_notifications}
            unreadCount={notifications.data?.unread_count ?? data.unread_notification_count}
            pinnedCount={notifications.data?.pinned_count ?? data.pinned_notifications.length}
            loading={notifications.isLoading}
            onUpdate={update}
          />
        </div>
      ) : null}
    </div>
  );
}

function MorningBrief({ data }: { data: DailyBriefingResponse }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-5 w-5" />
          Morning Brief
        </CardTitle>
        <CardDescription>
          {data.ai_narrative.available
            ? `${data.ai_narrative.provider} - ${data.ai_narrative.model}`
            : 'Deterministic briefing'}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm leading-6">{data.morning_summary}</p>
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Metric label="Due today" value={data.followups_due_today.length} />
          <Metric label="Overdue" value={data.overdue_followups.length} />
          <Metric label="Interviews" value={data.upcoming_interviews.length} />
          <Metric label="Unread" value={data.unread_notification_count} />
        </div>
        <div className="space-y-2">
          {data.ai_recommendations.map((item) => (
            <div key={item} className="rounded-md border p-3 text-sm">
              {item}
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="text-2xl font-semibold">{value}</div>
    </div>
  );
}

function PriorityCards({ items }: { items: BriefingItem[] }) {
  if (!items.length) {
    return <EmptyState title="No priorities yet" />;
  }
  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
      {items.slice(0, 6).map((item) => (
        <Card key={item.id}>
          <CardContent className="space-y-3 p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="font-medium">{item.title}</div>
                <div className="mt-1 text-sm text-muted-foreground">{item.detail}</div>
              </div>
              <Badge variant={priorityBadge(item.priority)}>{priorityLabel(item.priority)}</Badge>
            </div>
            {item.action_url ? (
              <Button size="sm" variant="outline" asChild>
                <Link to={item.action_url}>Open</Link>
              </Button>
            ) : null}
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function BriefingList({
  title,
  icon: Icon,
  items,
}: {
  title: string;
  icon: typeof Inbox;
  items: BriefingItem[];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className="h-5 w-5" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.length ? (
          items.map((item) => (
            <div key={item.id} className="rounded-md border p-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="text-sm font-medium">{item.title}</div>
                  <div className="text-sm text-muted-foreground">{item.detail}</div>
                </div>
                <Badge variant="outline">{item.priority}</Badge>
              </div>
            </div>
          ))
        ) : (
          <EmptyState title="Nothing scheduled" className="border-0 py-8" />
        )}
      </CardContent>
    </Card>
  );
}

function OpportunityHighlights({ data }: { data: DailyBriefingResponse }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Opportunity highlights</CardTitle>
        <CardDescription>Recently saved discoveries and recruiter activity</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-3 lg:grid-cols-2">
        {data.newly_discovered_opportunities.map((item) => (
          <div key={item.id} className="rounded-md border p-3">
            <div className="font-medium">{item.title}</div>
            <div className="text-sm text-muted-foreground">{item.company}</div>
          </div>
        ))}
        {data.new_recruiter_emails.map((item) => (
          <div key={item.id} className="rounded-md border p-3">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Mail className="h-4 w-4" />
              {item.sender}
            </div>
            <div className="mt-1 text-sm text-muted-foreground">{item.subject}</div>
          </div>
        ))}
        {!data.newly_discovered_opportunities.length && !data.new_recruiter_emails.length ? (
          <EmptyState title="No new activity" className="border-0 py-8 lg:col-span-2" />
        ) : null}
      </CardContent>
    </Card>
  );
}

function SkillAndResume({ data }: { data: DailyBriefingResponse }) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Skill updates</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {data.skill_trend_updates.length ? (
            data.skill_trend_updates.map((item) => (
              <div key={item.skill} className="flex items-center justify-between rounded-md border p-3">
                <div>
                  <div className="text-sm font-medium">{item.skill}</div>
                  <div className="text-xs text-muted-foreground">{item.category}</div>
                </div>
                <Badge variant="secondary">+{item.trend_delta}</Badge>
              </div>
            ))
          ) : (
            <EmptyState title="No rising skill signal" className="border-0 py-8" />
          )}
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Resume performance</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          {data.resume_performance_changes.length ? (
            data.resume_performance_changes.map((item) => (
              <div key={item.title} className="rounded-md border p-3">
                <div className="text-sm font-medium">{item.title}</div>
                <div className="text-sm text-muted-foreground">{item.detail}</div>
                {item.evidence ? (
                  <div className="mt-2 text-xs text-muted-foreground">{item.evidence}</div>
                ) : null}
              </div>
            ))
          ) : (
            <EmptyState title="No resume change yet" className="border-0 py-8" />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function NotificationCenter({
  items,
  unreadCount,
  pinnedCount,
  loading,
  onUpdate,
}: {
  items: NotificationItem[];
  unreadCount: number;
  pinnedCount: number;
  loading: boolean;
  onUpdate: (item: NotificationItem, patch: Partial<NotificationItem>) => void;
}) {
  return (
    <Card className="h-fit">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BellRing className="h-5 w-5" />
          Notifications
        </CardTitle>
        <CardDescription>
          {unreadCount} unread - {pinnedCount} pinned
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {loading ? (
          <Skeleton className="h-32 w-full" />
        ) : items.length ? (
          items.map((item) => (
            <div
              key={item.id}
              className={item.is_read ? 'rounded-md border p-3 opacity-75' : 'rounded-md border p-3'}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    {!item.is_read ? <Bell className="h-4 w-4 text-primary" /> : null}
                    <div className="truncate text-sm font-medium">{item.title}</div>
                  </div>
                  <div className="mt-1 text-sm text-muted-foreground">{item.message}</div>
                  <div className="mt-2 flex flex-wrap gap-2">
                    <Badge variant="outline">{item.category}</Badge>
                    <Badge variant={priorityBadge(item.priority)}>{item.priority}</Badge>
                  </div>
                </div>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onUpdate(item, { is_read: !item.is_read })}
                >
                  {item.is_read ? 'Unread' : 'Read'}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onUpdate(item, { is_pinned: !item.is_pinned })}
                >
                  <Pin className="h-4 w-4" />
                  {item.is_pinned ? 'Unpin' : 'Pin'}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => onUpdate(item, { is_dismissed: true })}
                >
                  <X className="h-4 w-4" />
                  Dismiss
                </Button>
              </div>
            </div>
          ))
        ) : (
          <EmptyState title="No notifications" className="border-0 py-8" />
        )}
      </CardContent>
    </Card>
  );
}

function BriefingSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-48 w-full" />
      <div className="grid gap-4 md:grid-cols-2">
        <Skeleton className="h-36 w-full" />
        <Skeleton className="h-36 w-full" />
      </div>
    </div>
  );
}
