import {
  Bell,
  BrainCircuit,
  Check,
  Clock,
  Download,
  FileText,
  Inbox,
  Mail,
  Pin,
  RefreshCw,
  Sparkles,
  Target,
  TrendingUp,
  Video,
  type LucideIcon,
} from 'lucide-react';
import type { Dispatch, ReactNode, SetStateAction } from 'react';
import { useMemo, useState } from 'react';
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
import { useCareerCopilot } from '@/features/career-copilot/hooks';
import {
  downloadDailyBriefing,
  formatDateTime,
  formatPercent,
  priorityVariant,
} from '@/features/career-copilot/lib';
import type {
  CareerCopilotResponse,
  PriorityItem,
} from '@/features/career-copilot/types';

export function CareerCopilotPage() {
  const { data, isLoading, isError, error, refetch, isFetching } =
    useCareerCopilot();
  const [pinned, setPinned] = useState<Set<string>>(() => new Set());
  const [completed, setCompleted] = useState<Set<string>>(() => new Set());

  const priorityCards = useMemo(() => {
    const priorities = data?.briefing.top_priorities ?? [];
    return [...priorities].sort((a, b) => {
      const pinnedDelta = Number(pinned.has(b.id)) - Number(pinned.has(a.id));
      if (pinnedDelta !== 0) return pinnedDelta;
      return a.rank - b.rank;
    });
  }, [data, pinned]);

  const toggleSet = (
    setter: Dispatch<SetStateAction<Set<string>>>,
    id: string,
  ) => {
    setter((current) => {
      const next = new Set(current);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Career Copilot"
        description="Your daily job-search briefing and action queue."
        actions={
          <>
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              disabled={isFetching}
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={!data}
              onClick={() => data && downloadDailyBriefing(data)}
            >
              <Download className="h-4 w-4" />
              Export
            </Button>
          </>
        }
      />

      {isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : isLoading ? (
        <CopilotSkeleton />
      ) : data ? (
        <div className="space-y-6">
          <MorningBrief data={data} />

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
            <MetricCard
              label="Active"
              value={data.today_metrics.active_applications}
              icon={Target}
            />
            <MetricCard
              label="Due Today"
              value={data.today_metrics.followups_due_today}
              icon={Bell}
              tone="warning"
            />
            <MetricCard
              label="Overdue"
              value={data.today_metrics.overdue_followups}
              icon={Clock}
              tone="destructive"
            />
            <MetricCard
              label="Interviews"
              value={data.today_metrics.upcoming_interviews}
              icon={Video}
            />
            <MetricCard
              label="Response"
              value={formatPercent(data.today_metrics.response_rate)}
              icon={TrendingUp}
            />
          </div>

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.15fr_0.85fr]">
            <PriorityPanel
              priorities={priorityCards}
              pinned={pinned}
              completed={completed}
              onPin={(id) => toggleSet(setPinned, id)}
              onComplete={(id) => toggleSet(setCompleted, id)}
            />
            <AIInsightPanel data={data} />
          </div>

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
            <TimelinePanel data={data} />
            <GmailPanel data={data} />
            <InterviewPanel data={data} />
          </div>

          <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
            <ActionsPanel />
            <SkillPanel data={data} />
            <PipelinePanel data={data} />
          </div>
        </div>
      ) : null}
    </div>
  );
}

function MorningBrief({ data }: { data: CareerCopilotResponse }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              Morning brief
            </CardTitle>
            <CardDescription>
              Generated {formatDateTime(data.generated_at)}
            </CardDescription>
          </div>
          {data.ai_insight_panel.available ? (
            <Badge variant="success">
              {data.ai_insight_panel.provider} · {data.ai_insight_panel.model}
            </Badge>
          ) : (
            <Badge variant="secondary">Deterministic mode</Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm leading-6 text-muted-foreground">
          {data.briefing.executive_summary}
        </p>
        {data.ai_insight_panel.caveats.length ? (
          <div className="flex flex-wrap gap-2">
            {data.ai_insight_panel.caveats.map((item) => (
              <Badge key={item} variant="outline">
                {item}
              </Badge>
            ))}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function PriorityPanel({
  priorities,
  pinned,
  completed,
  onPin,
  onComplete,
}: {
  priorities: PriorityItem[];
  pinned: Set<string>;
  completed: Set<string>;
  onPin: (id: string) => void;
  onComplete: (id: string) => void;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Priority cards</CardTitle>
        <CardDescription>Ranked actions for today</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {priorities.length ? (
          priorities.map((item) => {
            const done = completed.has(item.id);
            return (
              <div
                key={item.id}
                className="flex flex-col gap-3 rounded-lg border p-4 sm:flex-row sm:items-start sm:justify-between"
              >
                <div className="min-w-0 space-y-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant={priorityVariant(item.priority)}>
                      #{item.rank} {item.priority}
                    </Badge>
                    {pinned.has(item.id) ? <Badge variant="secondary">Pinned</Badge> : null}
                    {done ? <Badge variant="success">Complete</Badge> : null}
                  </div>
                  <div className={done ? 'opacity-60' : undefined}>
                    <h3 className="font-semibold">{item.title}</h3>
                    <p className="text-sm text-muted-foreground">{item.detail}</p>
                    <p className="mt-1 text-xs text-muted-foreground">
                      {item.reason}
                    </p>
                  </div>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <Button variant="ghost" size="icon" onClick={() => onPin(item.id)}>
                    <Pin className="h-4 w-4" />
                  </Button>
                  <Button
                    variant={done ? 'secondary' : 'outline'}
                    size="icon"
                    onClick={() => onComplete(item.id)}
                  >
                    <Check className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            );
          })
        ) : (
          <EmptyState
            icon={Target}
            title="No priorities"
            description="Add applications, interviews, or follow-ups to build a queue."
            className="border-0 py-10"
          />
        )}
      </CardContent>
    </Card>
  );
}

function AIInsightPanel({ data }: { data: CareerCopilotResponse }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BrainCircuit className="h-5 w-5" />
          AI insight panel
        </CardTitle>
        <CardDescription>Recommendations grounded in tracked data</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <Insight title="Skill focus" text={data.ai_insight_panel.skill_focus} />
        <Insight
          title="Resume recommendation"
          text={data.ai_insight_panel.resume_recommendation}
        />
        <Insight
          title="Interview prep"
          text={data.ai_insight_panel.interview_preparation_reminder}
        />
        <Insight
          title="Follow-up"
          text={data.ai_insight_panel.follow_up_reminder}
        />
      </CardContent>
    </Card>
  );
}

function TimelinePanel({ data }: { data: CareerCopilotResponse }) {
  return (
    <ListCard title="Upcoming timeline" description="Deadlines and recent activity">
      {data.upcoming_timeline.length ? (
        data.upcoming_timeline.map((item) => (
          <ListRow
            key={item.id}
            title={item.title}
            subtitle={`${item.kind} · ${formatDateTime(item.timestamp)}`}
          />
        ))
      ) : (
        <EmptyState title="No timeline items" className="border-0 py-8" />
      )}
    </ListCard>
  );
}

function GmailPanel({ data }: { data: CareerCopilotResponse }) {
  return (
    <ListCard title="Recent Gmail activity" description="Latest matched email signals">
      {data.recent_gmail_activity.length ? (
        data.recent_gmail_activity.map((item) => (
          <ListRow
            key={item.id}
            icon={Mail}
            title={item.subject}
            subtitle={`${item.sender} · ${formatDateTime(item.sent_at)}`}
          />
        ))
      ) : (
        <EmptyState
          icon={Inbox}
          title="No recent email"
          description="Connect or sync Gmail to surface recent job-search activity."
          className="border-0 py-8"
        />
      )}
    </ListCard>
  );
}

function InterviewPanel({ data }: { data: CareerCopilotResponse }) {
  return (
    <ListCard title="Upcoming interviews" description="Preparation targets">
      {data.upcoming_interviews.length ? (
        data.upcoming_interviews.map((item) => (
          <ListRow
            key={item.id}
            icon={Video}
            title={item.title}
            subtitle={`${item.interview_type ?? 'interview'} · ${formatDateTime(
              item.scheduled_at,
            )}`}
          />
        ))
      ) : (
        <EmptyState
          icon={Video}
          title="No interviews"
          description="Scheduled interviews will appear here."
          className="border-0 py-8"
        />
      )}
    </ListCard>
  );
}

function ActionsPanel() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick actions</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-2">
        <Button asChild variant="outline" className="justify-start">
          <Link to="/applications">Review applications</Link>
        </Button>
        <Button asChild variant="outline" className="justify-start">
          <Link to="/followups">Clear follow-ups</Link>
        </Button>
        <Button asChild variant="outline" className="justify-start">
          <Link to="/interview-prep">Open Interview Prep</Link>
        </Button>
        <Button asChild variant="outline" className="justify-start">
          <Link to="/career-intelligence">Open Career Intelligence</Link>
        </Button>
      </CardContent>
    </Card>
  );
}

function SkillPanel({ data }: { data: CareerCopilotResponse }) {
  return (
    <ListCard title="Skill focus" description="Most requested skills">
      {data.briefing.skill_focus.length ? (
        data.briefing.skill_focus.map((item) => (
          <ListRow
            key={item.skill}
            title={item.skill}
            subtitle={`${item.count} mentions · ${item.percentage ?? 0}%`}
          />
        ))
      ) : (
        <EmptyState
          icon={FileText}
          title="No skill signal"
          description="Run Resume Match or Interview Prep to collect job descriptions."
          className="border-0 py-8"
        />
      )}
    </ListCard>
  );
}

function PipelinePanel({ data }: { data: CareerCopilotResponse }) {
  return (
    <ListCard title="Application pipeline" description="Current status mix">
      {data.application_pipeline.length ? (
        data.application_pipeline.map((item) => (
          <ListRow
            key={item.status}
            title={item.status.replaceAll('_', ' ')}
            subtitle={`${item.count} application${item.count === 1 ? '' : 's'}`}
          />
        ))
      ) : (
        <EmptyState title="No applications" className="border-0 py-8" />
      )}
    </ListCard>
  );
}

function MetricCard({
  label,
  value,
  icon: Icon,
  tone = 'default',
}: {
  label: string;
  value: number | string;
  icon: LucideIcon;
  tone?: 'default' | 'warning' | 'destructive';
}) {
  const toneClass =
    tone === 'warning'
      ? 'bg-warning/15 text-warning'
      : tone === 'destructive'
        ? 'bg-destructive/10 text-destructive'
        : 'bg-primary/10 text-primary';
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-5">
        <div className={`flex h-11 w-11 items-center justify-center rounded-lg ${toneClass}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm text-muted-foreground">{label}</p>
          <p className="text-xl font-semibold tabular-nums">{value}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function Insight({ title, text }: { title: string; text: string }) {
  return (
    <div className="rounded-lg border p-3">
      <p className="text-sm font-medium">{title}</p>
      <p className="mt-1 text-sm leading-6 text-muted-foreground">{text}</p>
    </div>
  );
}

function ListCard({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        {description ? <CardDescription>{description}</CardDescription> : null}
      </CardHeader>
      <CardContent className="space-y-3">{children}</CardContent>
    </Card>
  );
}

function ListRow({
  title,
  subtitle,
  icon: Icon = Clock,
}: {
  title: string;
  subtitle?: string;
  icon?: LucideIcon;
}) {
  return (
    <div className="flex min-w-0 items-start gap-3">
      <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground">
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0">
        <p className="truncate text-sm font-medium">{title}</p>
        {subtitle ? (
          <p className="truncate text-xs text-muted-foreground">{subtitle}</p>
        ) : null}
      </div>
    </div>
  );
}

function CopilotSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-40 w-full" />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
        <Skeleton className="h-24" />
      </div>
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Skeleton className="h-96" />
        <Skeleton className="h-96" />
      </div>
    </div>
  );
}
