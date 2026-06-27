import {
  BrainCircuit,
  Download,
  Flame,
  Layers,
  Lightbulb,
  RefreshCw,
  Search,
} from 'lucide-react';
import type { ReactNode } from 'react';
import { useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
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
import { useJobIntelligence } from '@/features/job-intelligence/hooks';
import {
  compactParams,
  downloadJobIntelligence,
  formatPercent,
} from '@/features/job-intelligence/lib';
import type {
  DistributionItem,
  JobIntelligenceResponse,
  MissingSkill,
  SkillSignal,
} from '@/features/job-intelligence/types';

const tooltipStyle = {
  borderRadius: 8,
  border: '1px solid hsl(var(--border))',
  background: 'hsl(var(--popover))',
  color: 'hsl(var(--popover-foreground))',
  fontSize: 12,
};

const COLORS = [
  'hsl(var(--primary))',
  'hsl(var(--secondary-foreground))',
  'hsl(var(--success))',
  'hsl(var(--warning))',
  'hsl(var(--destructive))',
  'hsl(var(--muted-foreground))',
];

type JobIntelligenceFilterState = {
  date_from: string;
  date_to: string;
  industry: string;
  company: string;
  role: string;
};

export function JobIntelligencePage() {
  const [filters, setFilters] = useState<JobIntelligenceFilterState>({
    date_from: '',
    date_to: '',
    industry: '',
    company: '',
    role: '',
  });
  const params = useMemo(() => compactParams(filters), [filters]);
  const { data, isLoading, isError, error, refetch, isFetching } =
    useJobIntelligence(params);

  const trendData = useMemo(() => buildTrendData(data?.skill_signals ?? []), [data]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Job Intelligence"
        description="Structured skill-market intelligence from saved job descriptions."
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
              onClick={() => data && downloadJobIntelligence(data)}
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
        <JobIntelligenceSkeleton />
      ) : data ? (
        data.job_description_count === 0 ? (
          <EmptyState
            icon={Search}
            title="No saved job descriptions"
            description="Run Resume Match or Interview Prep with job descriptions to build the intelligence engine."
          />
        ) : (
          <>
            <ExecutiveSummary data={data} />

            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              <MetricCard label="Job descriptions" value={data.job_description_count} />
              <MetricCard label="Recognized skills" value={data.skill_signals.length} />
              <MetricCard label="Resume skills" value={data.resume_skill_count} />
            </div>

            <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.15fr_0.85fr]">
              <SkillHeatmap skills={data.skill_signals} />
              <MissingSkillsCard items={data.missing_skills} />
            </div>

            <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
              <ChartCard title="Technology trends" description="Top skill mentions over time">
                {trendData.length ? (
                  <ResponsiveContainer width="100%" height={320}>
                    <LineChart data={trendData}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} />
                      <XAxis dataKey="period" fontSize={12} />
                      <YAxis fontSize={12} allowDecimals={false} />
                      <Tooltip contentStyle={tooltipStyle} />
                      {data.skill_signals.slice(0, 5).map((skill, index) => (
                        <Line
                          key={skill.name}
                          type="monotone"
                          dataKey={skill.name}
                          stroke={COLORS[index % COLORS.length]}
                          strokeWidth={2}
                        />
                      ))}
                    </LineChart>
                  </ResponsiveContainer>
                ) : (
                  <EmptyState title="No trend data" className="border-0 py-10" />
                )}
              </ChartCard>

              <ChartCard title="Category mix" description="Demand by skill category">
                <ResponsiveContainer width="100%" height={320}>
                  <PieChart>
                    <Pie
                      data={data.category_breakdown}
                      dataKey="count"
                      nameKey="category"
                      innerRadius={60}
                      outerRadius={110}
                      paddingAngle={2}
                    >
                      {data.category_breakdown.map((item, index) => (
                        <Cell key={item.category} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip contentStyle={tooltipStyle} />
                  </PieChart>
                </ResponsiveContainer>
              </ChartCard>
            </div>

            <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
              <DistributionCard title="Industry breakdown" items={data.industry_breakdown} />
              <DistributionCard title="Company breakdown" items={data.company_breakdown} />
              <DistributionCard title="Role breakdown" items={data.role_breakdown} />
            </div>

            <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
              <ChartCard title="Top skills" description="Frequency across saved postings">
                <ResponsiveContainer width="100%" height={360}>
                  <BarChart data={data.skill_signals.slice(0, 12)} layout="vertical">
                    <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                    <XAxis type="number" fontSize={12} />
                    <YAxis dataKey="name" type="category" width={120} fontSize={12} />
                    <Tooltip contentStyle={tooltipStyle} />
                    <Bar dataKey="frequency" fill="hsl(var(--primary))" radius={[0, 6, 6, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </ChartCard>
              <AIRecommendations data={data} />
            </div>
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
  filters: JobIntelligenceFilterState;
  onChange: (filters: JobIntelligenceFilterState) => void;
}) {
  const setField = (field: keyof JobIntelligenceFilterState, value: string) =>
    onChange({ ...filters, [field]: value });
  return (
    <Card>
      <CardContent className="grid gap-4 p-4 md:grid-cols-2 xl:grid-cols-5">
        <Field label="From" type="date" value={filters.date_from} onChange={(v) => setField('date_from', v)} />
        <Field label="To" type="date" value={filters.date_to} onChange={(v) => setField('date_to', v)} />
        <Field label="Industry" value={filters.industry} onChange={(v) => setField('industry', v)} />
        <Field label="Company" value={filters.company} onChange={(v) => setField('company', v)} />
        <Field label="Role" value={filters.role} onChange={(v) => setField('role', v)} />
      </CardContent>
    </Card>
  );
}

function Field({
  label,
  value,
  onChange,
  type = 'text',
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
}) {
  return (
    <div className="space-y-2">
      <Label>{label}</Label>
      <Input type={type} value={value} onChange={(event) => onChange(event.target.value)} />
    </div>
  );
}

function ExecutiveSummary({ data }: { data: JobIntelligenceResponse }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BrainCircuit className="h-5 w-5" />
          Executive summary
        </CardTitle>
        <CardDescription>
          {data.ai_interpretation.available
            ? `${data.ai_interpretation.provider} - ${data.ai_interpretation.model}`
            : 'Deterministic interpretation'}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <p className="text-sm leading-6 text-muted-foreground">
          {data.ai_interpretation.executive_summary}
        </p>
        {data.ai_interpretation.caveats.length ? (
          <div className="flex flex-wrap gap-2">
            {data.ai_interpretation.caveats.map((item) => (
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

function SkillHeatmap({ skills }: { skills: SkillSignal[] }) {
  const max = Math.max(...skills.map((skill) => skill.frequency), 1);
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Flame className="h-5 w-5" />
          Skill heatmap
        </CardTitle>
        <CardDescription>Intensity reflects frequency in saved postings</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">
          {skills.slice(0, 24).map((skill) => {
            const opacity = 0.15 + (skill.frequency / max) * 0.75;
            return (
              <div
                key={`${skill.category}-${skill.name}`}
                className="rounded-md border p-3"
                style={{ backgroundColor: `hsl(var(--primary) / ${opacity})` }}
              >
                <p className="truncate text-sm font-medium">{skill.name}</p>
                <p className="text-xs text-muted-foreground">
                  {skill.category} · {skill.frequency}
                </p>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}

function MissingSkillsCard({ items }: { items: MissingSkill[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Missing skills</CardTitle>
        <CardDescription>Market signals absent from extracted resume skills</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.length ? (
          items.slice(0, 10).map((item) => (
            <div key={item.name} className="rounded-lg border p-3">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="font-medium">{item.name}</p>
                  <p className="text-xs text-muted-foreground">{item.category}</p>
                </div>
                <Badge variant="secondary">{formatPercent(item.market_percentage)}</Badge>
              </div>
              <p className="mt-2 text-xs leading-5 text-muted-foreground">{item.reason}</p>
            </div>
          ))
        ) : (
          <EmptyState
            icon={Layers}
            title="No deterministic gaps"
            description="Your extracted resume skills cover the recognized market signals."
            className="border-0 py-10"
          />
        )}
      </CardContent>
    </Card>
  );
}

function DistributionCard({ title, items }: { title: string; items: DistributionItem[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.length ? (
          items.map((item) => (
            <div key={item.name} className="space-y-1">
              <div className="flex justify-between gap-3 text-sm">
                <span className="truncate">{item.name}</span>
                <span className="tabular-nums text-muted-foreground">{item.count}</span>
              </div>
              <div className="h-2 rounded-full bg-muted">
                <div
                  className="h-2 rounded-full bg-primary"
                  style={{ width: `${item.percentage ?? 0}%` }}
                />
              </div>
            </div>
          ))
        ) : (
          <EmptyState title="No data" className="border-0 py-8" />
        )}
      </CardContent>
    </Card>
  );
}

function AIRecommendations({ data }: { data: JobIntelligenceResponse }) {
  const groups = [
    ['Learning priorities', data.ai_interpretation.top_learning_priorities],
    ['Emerging technologies', data.ai_interpretation.emerging_technologies],
    ['Resume recommendations', data.ai_interpretation.resume_recommendations],
    ['Skill investments', data.ai_interpretation.skill_investment_suggestions],
    ['Career direction', data.ai_interpretation.career_direction_suggestions],
  ] as const;
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Lightbulb className="h-5 w-5" />
          AI recommendations
        </CardTitle>
        <CardDescription>Interpretation of deterministic analytics</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {groups.map(([title, items]) => (
          <div key={title} className="space-y-2">
            <h3 className="text-sm font-semibold">{title}</h3>
            {items.length ? (
              <ul className="space-y-1 text-sm text-muted-foreground">
                {items.map((item) => (
                  <li key={item}>{item}</li>
                ))}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">No signal yet.</p>
            )}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function MetricCard({ label, value }: { label: string; value: number }) {
  return (
    <Card>
      <CardContent className="p-5">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className="mt-1 text-2xl font-semibold tabular-nums">{value}</p>
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

function buildTrendData(skills: SkillSignal[]) {
  const periods = Array.from(
    new Set(skills.flatMap((skill) => skill.trend.map((point) => point.period))),
  ).sort();
  return periods.map((period) => {
    const row: Record<string, string | number> = { period };
    for (const skill of skills.slice(0, 5)) {
      row[skill.name] = skill.trend.find((point) => point.period === period)?.count ?? 0;
    }
    return row;
  });
}

function JobIntelligenceSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-32 w-full" />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
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
