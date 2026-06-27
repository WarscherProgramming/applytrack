import {
  BarChart3,
  BrainCircuit,
  Download,
  FileSignature,
  FileText,
  Lightbulb,
  RefreshCw,
  Target,
  TrendingUp,
  type LucideIcon,
} from 'lucide-react';
import type { ReactNode } from 'react';
import { useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

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
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { useCareerIntelligence } from '@/features/career-intelligence/hooks';
import {
  compactParams,
  downloadCareerIntelligence,
  formatNumber,
  formatPercent,
} from '@/features/career-intelligence/lib';
import type {
  CountInsight,
  DocumentPerformance,
  SegmentInsight,
} from '@/features/career-intelligence/types';

const tooltipStyle = {
  borderRadius: 8,
  border: '1px solid hsl(var(--border))',
  background: 'hsl(var(--popover))',
  color: 'hsl(var(--popover-foreground))',
  fontSize: 12,
};

const chartColor = 'hsl(var(--primary))';
const secondaryChartColor = 'hsl(var(--secondary-foreground))';

interface CareerFilters {
  date_from: string;
  date_to: string;
  compare_date_from: string;
  compare_date_to: string;
}

export function CareerIntelligencePage() {
  const [filters, setFilters] = useState<CareerFilters>({
    date_from: '',
    date_to: '',
    compare_date_from: '',
    compare_date_to: '',
  });
  const params = useMemo(() => compactParams(filters), [filters]);
  const { data, isLoading, isError, error, refetch, isFetching } =
    useCareerIntelligence(params);

  const rateChartData = data
    ? [
        { name: 'Response', value: data.application_metrics.response_rate.value ?? 0 },
        { name: 'Interview', value: data.application_metrics.interview_rate.value ?? 0 },
        { name: 'Offer', value: data.application_metrics.offer_rate.value ?? 0 },
        { name: 'Reject', value: data.application_metrics.rejection_rate.value ?? 0 },
        { name: 'Ghost', value: data.application_metrics.ghost_rate.value ?? 0 },
      ]
    : [];

  const skillData =
    data?.skill_intelligence.most_requested_skills.map((item) => ({
      name: item.name,
      count: item.count,
    })) ?? [];

  const industryData =
    data?.company_insights.most_responsive_industries.map((item) => ({
      name: item.name,
      response_rate: item.response_rate ?? 0,
      total: item.total_applications,
    })) ?? [];

  const trendData =
    data?.skill_intelligence.trending_technologies.map((item) => ({
      name: item.name,
      current: item.current_count,
      previous: item.previous_count,
    })) ?? [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Career Intelligence"
        description="Search-wide analytics and AI recommendations from your tracked history."
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
              onClick={() => data && downloadCareerIntelligence(data)}
            >
              <Download className="h-4 w-4" />
              Export
            </Button>
          </>
        }
      />

      <FilterBar filters={filters} onChange={setFilters} />

      {isError ? (
        <ErrorState error={error} onRetry={refetch} />
      ) : isLoading ? (
        <DashboardSkeleton />
      ) : data ? (
        data.application_metrics.total_applications === 0 &&
        data.skill_intelligence.job_description_count === 0 ? (
          <EmptyState
            icon={BrainCircuit}
            title="No intelligence yet"
            description="Tracked applications, synced email, interviews, and AI histories will populate this dashboard."
          />
        ) : (
          <>
            <ExecutiveSummary data={data.ai_recommendations} />

            <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
              <KpiCard
                label="Applications"
                value={data.application_metrics.total_applications.toLocaleString()}
                hint={`${data.application_metrics.active_applications} active`}
                icon={Target}
              />
              <KpiCard
                label="Response rate"
                value={formatPercent(data.application_metrics.response_rate.value)}
                hint={`${data.application_metrics.response_rate.numerator}/${data.application_metrics.response_rate.denominator}`}
                icon={TrendingUp}
              />
              <KpiCard
                label="Interview rate"
                value={formatPercent(data.application_metrics.interview_rate.value)}
                hint={`${data.application_metrics.interview_rate.numerator}/${data.application_metrics.interview_rate.denominator}`}
                icon={BarChart3}
              />
              <KpiCard
                label="Days to first response"
                value={formatNumber(
                  data.application_metrics.average_days_until_first_response,
                )}
                hint="Average from timestamped email/interview signals"
                icon={RefreshCw}
              />
            </div>

            <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
              <ChartCard title="Conversion rates" description="Current application outcomes">
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={rateChartData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" fontSize={12} />
                    <YAxis fontSize={12} tickFormatter={(value) => `${value}%`} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Bar dataKey="value" fill={chartColor} radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>

              <ChartCard title="Compare periods" description="Current vs comparison period">
                {data.comparison ? (
                  <ResponsiveContainer width="100%" height={280}>
                    <LineChart data={data.comparison.metrics}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="name" fontSize={12} />
                      <YAxis fontSize={12} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Line
                        type="monotone"
                        dataKey="current"
                        stroke={chartColor}
                        strokeWidth={2}
                      />
                      <Line
                        type="monotone"
                        dataKey="previous"
                        stroke={secondaryChartColor}
                        strokeWidth={2}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyState
                    icon={TrendingUp}
                    title="No comparison selected"
                    description="Add comparison dates to see period-over-period movement."
                    className="border-0 py-10"
                  />
                )}
              </ChartCard>
            </div>

            <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
              <PerformanceCard
                title="Resume performance"
                icon={FileText}
                items={data.resume_insights.items}
              />
              <PerformanceCard
                title="Cover letter performance"
                icon={FileSignature}
                items={data.cover_letter_insights.items}
              />
            </div>

            <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
              <ChartCard
                title="Skill trends"
                description={`${data.skill_intelligence.job_description_count} stored job descriptions`}
              >
                {skillData.length ? (
                  <ResponsiveContainer width="100%" height={320}>
                    <BarChart data={skillData} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                      <XAxis type="number" fontSize={12} />
                      <YAxis dataKey="name" type="category" width={110} fontSize={12} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar dataKey="count" fill={chartColor} radius={[0, 6, 6, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyState
                    icon={BarChart3}
                    title="No job descriptions"
                    description="Resume Match and Interview Prep histories provide skill intelligence."
                    className="border-0 py-10"
                  />
                )}
              </ChartCard>

              <ChartCard title="Industry trends" description="Response rate by industry">
                {industryData.length ? (
                  <ResponsiveContainer width="100%" height={320}>
                    <BarChart data={industryData} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                      <XAxis type="number" fontSize={12} tickFormatter={(v) => `${v}%`} />
                      <YAxis dataKey="name" type="category" width={120} fontSize={12} />
                      <Tooltip contentStyle={tooltipStyle} />
                      <Bar
                        dataKey="response_rate"
                        fill={chartColor}
                        radius={[0, 6, 6, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyState
                    icon={BarChart3}
                    title="No industry data"
                    description="Add company industries to compare response patterns."
                    className="border-0 py-10"
                  />
                )}
              </ChartCard>
            </div>

            <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
              <RankedList title="Fastest company responses" items={data.company_insights.fastest_response_companies} />
              <CountList title="Missing skills" items={data.skill_intelligence.missing_skills} />
              <CountList
                title="Interview topics"
                items={data.interview_intelligence.common_technical_topics}
              />
            </div>

            <ChartCard title="Technology movement" description="Current vs comparison counts">
              {trendData.length ? (
                <ResponsiveContainer width="100%" height={280}>
                  <BarChart data={trendData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} />
                    <XAxis dataKey="name" fontSize={12} />
                    <YAxis fontSize={12} allowDecimals={false} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Bar dataKey="previous" fill={secondaryChartColor} radius={[6, 6, 0, 0]} />
                    <Bar dataKey="current" fill={chartColor} radius={[6, 6, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : (
                <EmptyState
                  icon={TrendingUp}
                  title="No technology trend"
                  description="Add comparison dates or more stored job descriptions."
                  className="border-0 py-10"
                />
              )}
            </ChartCard>

            <RecommendationsCard data={data.ai_recommendations} />
          </>
        )
      ) : null}
    </div>
  );
}

function FilterBar({
  filters,
  onChange,
}: {
  filters: CareerFilters;
  onChange: (filters: CareerFilters) => void;
}) {
  const setField = (field: keyof CareerFilters, value: string) =>
    onChange({ ...filters, [field]: value });

  return (
    <Card>
      <CardContent className="grid gap-4 p-4 md:grid-cols-2 xl:grid-cols-4">
        <DateField
          label="From"
          value={filters.date_from}
          onChange={(value) => setField('date_from', value)}
        />
        <DateField
          label="To"
          value={filters.date_to}
          onChange={(value) => setField('date_to', value)}
        />
        <DateField
          label="Compare from"
          value={filters.compare_date_from}
          onChange={(value) => setField('compare_date_from', value)}
        />
        <DateField
          label="Compare to"
          value={filters.compare_date_to}
          onChange={(value) => setField('compare_date_to', value)}
        />
      </CardContent>
    </Card>
  );
}

function DateField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <Input type="date" value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function KpiCard({
  label,
  value,
  hint,
  icon: Icon,
}: {
  label: string;
  value: string;
  hint: string;
  icon: LucideIcon;
}) {
  return (
    <Card>
      <CardContent className="flex items-center gap-4 p-5">
        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
          <Icon className="h-5 w-5" />
        </div>
        <div className="min-w-0 space-y-1">
          <p className="truncate text-sm text-muted-foreground">{label}</p>
          <p className="text-xl font-semibold tabular-nums">{value}</p>
          <p className="truncate text-xs text-muted-foreground">{hint}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function ChartCard({
  title,
  description,
  children,
}: {
  title: string;
  description: string;
  children: ReactNode;
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

function ExecutiveSummary({
  data,
}: {
  data: {
    executive_summary: string;
    available: boolean;
    provider: string | null;
    model: string | null;
    caveats: string[];
  };
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BrainCircuit className="h-5 w-5" />
          Executive summary
        </CardTitle>
        <CardDescription>
          {data.available && data.provider && data.model
            ? `${data.provider} · ${data.model}`
            : 'Deterministic analytics'}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm leading-6 text-muted-foreground">{data.executive_summary}</p>
        {data.caveats.length ? (
          <div className="flex flex-wrap gap-2">
            {data.caveats.map((caveat) => (
              <Badge key={caveat} variant="secondary">
                {caveat}
              </Badge>
            ))}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

function PerformanceCard({
  title,
  icon: Icon,
  items,
}: {
  title: string;
  icon: LucideIcon;
  items: DocumentPerformance[];
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className="h-5 w-5" />
          {title}
        </CardTitle>
        <CardDescription>Linked application outcomes by version</CardDescription>
      </CardHeader>
      <CardContent>
        {items.length ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-muted-foreground">
                  <th className="py-2 pr-3 font-medium">Version</th>
                  <th className="py-2 pr-3 font-medium">Apps</th>
                  <th className="py-2 pr-3 font-medium">Response</th>
                  <th className="py-2 pr-3 font-medium">Interview</th>
                  <th className="py-2 font-medium">Offer</th>
                </tr>
              </thead>
              <tbody>
                {items.slice(0, 8).map((item) => (
                  <tr key={item.id} className="border-b last:border-0">
                    <td className="max-w-[220px] truncate py-2 pr-3">
                      {item.name} v{item.version}
                    </td>
                    <td className="py-2 pr-3 tabular-nums">
                      {item.submitted_applications}
                    </td>
                    <td className="py-2 pr-3 tabular-nums">
                      {formatPercent(item.response_rate)}
                    </td>
                    <td className="py-2 pr-3 tabular-nums">
                      {formatPercent(item.interview_rate)}
                    </td>
                    <td className="py-2 tabular-nums">
                      {formatPercent(item.offer_rate)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <EmptyState
            icon={Icon}
            title="No linked versions"
            description="Link submitted documents to applications to compare performance."
            className="border-0 py-10"
          />
        )}
      </CardContent>
    </Card>
  );
}

function RankedList({ title, items }: { title: string; items: SegmentInsight[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.length ? (
          items.map((item) => (
            <div key={item.name} className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate text-sm font-medium">{item.name}</p>
                <p className="text-xs text-muted-foreground">
                  {item.responses}/{item.total_applications} responses
                </p>
              </div>
              <Badge variant="secondary">
                {item.average_days_until_first_response === null
                  ? formatPercent(item.response_rate)
                  : `${item.average_days_until_first_response}d`}
              </Badge>
            </div>
          ))
        ) : (
          <EmptyState
            title="No ranked data"
            description="More timestamped responses will fill this list."
            className="border-0 py-8"
          />
        )}
      </CardContent>
    </Card>
  );
}

function CountList({ title, items }: { title: string; items: CountInsight[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.length ? (
          items.slice(0, 8).map((item) => (
            <div key={item.name} className="flex items-center justify-between gap-3">
              <span className="min-w-0 truncate text-sm">{item.name}</span>
              <Badge variant="secondary">{item.count}</Badge>
            </div>
          ))
        ) : (
          <EmptyState
            title="No signals"
            description="The next AI histories and interviews will add signals."
            className="border-0 py-8"
          />
        )}
      </CardContent>
    </Card>
  );
}

function RecommendationsCard({
  data,
}: {
  data: {
    recommendations: Array<{ title: string; detail: string; evidence: string }>;
  };
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5" />
          AI recommendations
        </CardTitle>
        <CardDescription>Grounded in computed analytics</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-2">
        {data.recommendations.map((item) => (
          <div key={item.title} className="rounded-lg border p-4">
            <div className="space-y-2">
              <h3 className="font-semibold">{item.title}</h3>
              <p className="text-sm leading-6 text-muted-foreground">{item.detail}</p>
              <Badge variant="outline">{item.evidence}</Badge>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-32 w-full" />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
        <Skeleton className="h-28" />
      </div>
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Skeleton className="h-80" />
        <Skeleton className="h-80" />
      </div>
    </div>
  );
}
