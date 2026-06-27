import {
  Briefcase,
  ExternalLink,
  GitCompare,
  RefreshCw,
  Save,
  Search,
  Sparkles,
} from 'lucide-react';
import type { ReactNode } from 'react';
import { useMemo, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import {
  useOpportunitySearch,
  useSaveOpportunity,
} from '@/features/opportunity-discovery/hooks';
import {
  buildSearchRequest,
  toggleProvider,
  type OpportunityDiscoveryFilters,
} from '@/features/opportunity-discovery/lib';
import type {
  JobProviderName,
  OpportunitySearchResponse,
  ScoredOpportunity,
  WorkMode,
} from '@/features/opportunity-discovery/types';
import { useToast } from '@/hooks/use-toast';

const initialFilters: OpportunityDiscoveryFilters = {
  query: '',
  greenhouse_boards: '',
  lever_companies: '',
  ashby_boards: '',
  rss_feeds: '',
  providers: [],
  remote: 'any',
  location: '',
  min_salary: '',
  technologies: '',
  preferred_location: '',
  preferred_job_type: '',
  preferred_industry: '',
  limit: '25',
};

const providerOptions: { id: JobProviderName; label: string }[] = [
  { id: 'greenhouse', label: 'Greenhouse' },
  { id: 'lever', label: 'Lever' },
  { id: 'ashby', label: 'Ashby' },
  { id: 'rss', label: 'RSS' },
];

const colors = [
  'hsl(var(--primary))',
  'hsl(var(--success))',
  'hsl(var(--warning))',
  'hsl(var(--destructive))',
  'hsl(var(--muted-foreground))',
];

const tooltipStyle = {
  borderRadius: 8,
  border: '1px solid hsl(var(--border))',
  background: 'hsl(var(--popover))',
  color: 'hsl(var(--popover-foreground))',
  fontSize: 12,
};

export function OpportunityDiscoveryPage() {
  const [filters, setFilters] = useState(initialFilters);
  const [data, setData] = useState<OpportunitySearchResponse | null>(null);
  const [compareIds, setCompareIds] = useState<string[]>([]);
  const [quickId, setQuickId] = useState<string | null>(null);
  const search = useOpportunitySearch();
  const save = useSaveOpportunity();
  const { toast } = useToast();

  const compared = useMemo(
    () => data?.items.filter((item) => compareIds.includes(item.posting.id)) ?? [],
    [compareIds, data],
  );
  const quickItem = useMemo(
    () => data?.items.find((item) => item.posting.id === quickId) ?? null,
    [data, quickId],
  );

  const runSearch = () => {
    search.mutate(buildSearchRequest(filters), {
      onSuccess: (payload) => {
        setData(payload);
        setCompareIds([]);
        setQuickId(payload.items[0]?.posting.id ?? null);
      },
    });
  };

  const update = <K extends keyof OpportunityDiscoveryFilters>(
    key: K,
    value: OpportunityDiscoveryFilters[K],
  ) => setFilters((current) => ({ ...current, [key]: value }));

  const saveOpportunity = (item: ScoredOpportunity) => {
    save.mutate(
      {
        posting: item.posting,
        resume_id: item.score.recommended_resume_id,
        cover_letter_id: item.score.suggested_cover_letter_id,
      },
      {
        onSuccess: (payload) => {
          toast({
            title: 'Added to Applications',
            description: payload.application.job_title,
          });
        },
        onError: () => {
          toast({
            variant: 'destructive',
            title: 'Could not add opportunity',
          });
        },
      },
    );
  };

  const toggleCompare = (id: string) => {
    setCompareIds((current) =>
      current.includes(id)
        ? current.filter((item) => item !== id)
        : [...current, id].slice(-3),
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Opportunity Discovery"
        description="Find public jobs, score fit, compare options, and add the best roles to your pipeline."
        actions={
          <Button onClick={runSearch} disabled={search.isPending}>
            {search.isPending ? (
              <RefreshCw className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            Search
          </Button>
        }
      />

      <DiscoveryFilters filters={filters} update={update} />

      {search.isError ? (
        <ErrorState error={search.error} onRetry={runSearch} />
      ) : search.isPending ? (
        <DiscoverySkeleton />
      ) : data ? (
        data.total === 0 ? (
          <EmptyState
            icon={Search}
            title="No opportunities found"
            description="Add at least one provider source such as a Greenhouse board, Lever company, Ashby board, or RSS feed."
          />
        ) : (
          <>
            <ProviderIssues data={data} />
            <SummaryCharts data={data} />

            <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1fr_360px]">
              <div className="space-y-4">
                {data.items.map((item) => (
                  <OpportunityCard
                    key={item.posting.id}
                    item={item}
                    compared={compareIds.includes(item.posting.id)}
                    quickActive={quickId === item.posting.id}
                    saving={save.isPending}
                    onCompare={() => toggleCompare(item.posting.id)}
                    onQuick={() => setQuickId(item.posting.id)}
                    onSave={() => saveOpportunity(item)}
                  />
                ))}
              </div>
              <div className="space-y-4">
                <ComparePanel items={compared} />
                <QuickMatchPanel item={quickItem} />
              </div>
            </div>
          </>
        )
      ) : (
        <EmptyState
          icon={Briefcase}
          title="Configure a discovery source"
          description="Enter public board identifiers or feed URLs, then run search to score opportunities."
        />
      )}
    </div>
  );
}

function DiscoveryFilters({
  filters,
  update,
}: {
  filters: OpportunityDiscoveryFilters;
  update: <K extends keyof OpportunityDiscoveryFilters>(
    key: K,
    value: OpportunityDiscoveryFilters[K],
  ) => void;
}) {
  return (
    <Card>
      <CardContent className="space-y-5 p-4">
        <div className="grid gap-4 lg:grid-cols-4">
          <Field
            label="Search"
            value={filters.query}
            onChange={(value) => update('query', value)}
          />
          <Field
            label="Location"
            value={filters.location}
            onChange={(value) => update('location', value)}
          />
          <Field
            label="Minimum salary"
            type="number"
            value={filters.min_salary}
            onChange={(value) => update('min_salary', value)}
          />
          <div className="space-y-2">
            <Label>Remote filter</Label>
            <Select
              value={filters.remote}
              onValueChange={(value) => update('remote', value as 'any' | WorkMode)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="any">Any</SelectItem>
                <SelectItem value="remote">Remote</SelectItem>
                <SelectItem value="hybrid">Hybrid</SelectItem>
                <SelectItem value="onsite">Onsite</SelectItem>
                <SelectItem value="unknown">Unknown</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid gap-4 lg:grid-cols-4">
          <Field
            label="Greenhouse boards"
            value={filters.greenhouse_boards}
            onChange={(value) => update('greenhouse_boards', value)}
          />
          <Field
            label="Lever companies"
            value={filters.lever_companies}
            onChange={(value) => update('lever_companies', value)}
          />
          <Field
            label="Ashby boards"
            value={filters.ashby_boards}
            onChange={(value) => update('ashby_boards', value)}
          />
          <Field
            label="RSS feeds"
            value={filters.rss_feeds}
            onChange={(value) => update('rss_feeds', value)}
          />
        </div>

        <div className="grid gap-4 lg:grid-cols-5">
          <Field
            label="Technology filter"
            value={filters.technologies}
            onChange={(value) => update('technologies', value)}
          />
          <Field
            label="Preferred location"
            value={filters.preferred_location}
            onChange={(value) => update('preferred_location', value)}
          />
          <Field
            label="Preferred job type"
            value={filters.preferred_job_type}
            onChange={(value) => update('preferred_job_type', value)}
          />
          <Field
            label="Preferred industry"
            value={filters.preferred_industry}
            onChange={(value) => update('preferred_industry', value)}
          />
          <Field
            label="Limit"
            type="number"
            value={filters.limit}
            onChange={(value) => update('limit', value)}
          />
        </div>

        <div className="flex flex-wrap gap-2">
          {providerOptions.map((provider) => (
            <label
              key={provider.id}
              className="flex h-9 items-center gap-2 rounded-md border px-3 text-sm"
            >
              <input
                type="checkbox"
                checked={filters.providers.includes(provider.id)}
                onChange={() =>
                  update('providers', toggleProvider(filters.providers, provider.id))
                }
              />
              {provider.label}
            </label>
          ))}
        </div>
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

function OpportunityCard({
  item,
  compared,
  quickActive,
  saving,
  onCompare,
  onQuick,
  onSave,
}: {
  item: ScoredOpportunity;
  compared: boolean;
  quickActive: boolean;
  saving: boolean;
  onCompare: () => void;
  onQuick: () => void;
  onSave: () => void;
}) {
  const { posting, score, ai_explanation } = item;
  return (
    <Card>
      <CardHeader className="space-y-3">
        <div className="flex flex-col gap-3 md:flex-row md:items-start md:justify-between">
          <div className="min-w-0 space-y-2">
            <CardTitle className="text-xl">{posting.title}</CardTitle>
            <CardDescription>
              {posting.company}
              {posting.location ? ` - ${posting.location}` : ''}
            </CardDescription>
            <div className="flex flex-wrap gap-2">
              <Badge variant="secondary">{posting.provider}</Badge>
              <Badge variant="outline">{posting.work_mode}</Badge>
              {posting.salary ? <Badge variant="outline">{posting.salary}</Badge> : null}
              {posting.employment_type ? (
                <Badge variant="outline">{posting.employment_type}</Badge>
              ) : null}
            </div>
          </div>
          <div className="text-left md:text-right">
            <div className="text-3xl font-semibold">
              {score.overall_match_percent}%
            </div>
            <div className="text-xs text-muted-foreground">AI Match</div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="line-clamp-3 text-sm text-muted-foreground">
          {ai_explanation.summary}
        </p>
        <div className="grid gap-3 md:grid-cols-3">
          <Metric label="Resume" value={score.recommended_resume_name ?? 'No resume'} />
          <Metric
            label="Cover letter"
            value={score.suggested_cover_letter_name ?? 'No template'}
          />
          <Metric
            label="Historical response"
            value={
              score.historical_response_rate === null
                ? 'No history'
                : `${score.historical_response_rate.toFixed(1)}%`
            }
          />
        </div>
        <div className="flex flex-wrap gap-2">
          {posting.skills.slice(0, 10).map((skill) => (
            <Badge key={`${posting.id}-${skill.name}`} variant="outline">
              {skill.name}
            </Badge>
          ))}
        </div>
        <div className="flex flex-wrap gap-2">
          <Button size="sm" onClick={onSave} disabled={saving}>
            <Save className="h-4 w-4" />
            Add to Applications
          </Button>
          <Button
            size="sm"
            variant={quickActive ? 'secondary' : 'outline'}
            onClick={onQuick}
          >
            <Sparkles className="h-4 w-4" />
            Quick Resume Match
          </Button>
          <Button
            size="sm"
            variant={compared ? 'secondary' : 'outline'}
            onClick={onCompare}
          >
            <GitCompare className="h-4 w-4" />
            Compare
          </Button>
          <Button size="sm" variant="outline" asChild>
            <a href={posting.job_url} target="_blank" rel="noreferrer">
              <ExternalLink className="h-4 w-4" />
              Open
            </a>
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="truncate text-sm font-medium">{value}</div>
    </div>
  );
}

function ComparePanel({ items }: { items: ScoredOpportunity[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Compare</CardTitle>
        <CardDescription>Up to three selected opportunities</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {items.length === 0 ? (
          <EmptyState title="No comparison selected" className="border-0 py-8" />
        ) : (
          items.map((item) => (
            <div key={item.posting.id} className="rounded-md border p-3">
              <div className="flex items-center justify-between gap-3">
                <div className="min-w-0">
                  <div className="truncate text-sm font-medium">{item.posting.title}</div>
                  <div className="truncate text-xs text-muted-foreground">
                    {item.posting.company}
                  </div>
                </div>
                <Badge>{item.score.overall_match_percent}%</Badge>
              </div>
              <div className="mt-2 text-xs text-muted-foreground">
                Missing: {item.score.top_missing_skills.join(', ') || 'None detected'}
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}

function QuickMatchPanel({ item }: { item: ScoredOpportunity | null }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Resume Match</CardTitle>
        <CardDescription>Deterministic resume overlap and gaps</CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {!item ? (
          <EmptyState title="Select a job" className="border-0 py-8" />
        ) : (
          <>
            <div className="text-3xl font-semibold">
              {item.score.resume_match_score ?? 0}%
            </div>
            <div className="text-sm text-muted-foreground">
              {item.score.reasoning[0]}
            </div>
            <div>
              <div className="mb-2 text-xs font-medium uppercase text-muted-foreground">
                Matched skills
              </div>
              <div className="flex flex-wrap gap-2">
                {item.score.matched_skills.map((skill) => (
                  <Badge key={skill} variant="secondary">
                    {skill}
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <div className="mb-2 text-xs font-medium uppercase text-muted-foreground">
                Missing skills
              </div>
              <div className="flex flex-wrap gap-2">
                {item.score.top_missing_skills.length ? (
                  item.score.top_missing_skills.map((skill) => (
                    <Badge key={skill} variant="outline">
                      {skill}
                    </Badge>
                  ))
                ) : (
                  <span className="text-sm text-muted-foreground">None detected</span>
                )}
              </div>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

function SummaryCharts({ data }: { data: OpportunitySearchResponse }) {
  return (
    <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
      <ChartCard title="Top technologies">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={data.top_technologies}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="name" fontSize={12} />
            <YAxis allowDecimals={false} fontSize={12} />
            <Tooltip contentStyle={tooltipStyle} />
            <Bar dataKey="count" fill="hsl(var(--primary))" radius={[6, 6, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>
      <ChartCard title="Top industries">
        <ResponsiveContainer width="100%" height={240}>
          <PieChart>
            <Pie data={data.top_industries} dataKey="count" nameKey="name" outerRadius={90}>
              {data.top_industries.map((item, index) => (
                <Cell key={item.name} fill={colors[index % colors.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={tooltipStyle} />
          </PieChart>
        </ResponsiveContainer>
      </ChartCard>
      <ChartCard title="Top locations">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={data.top_locations} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" allowDecimals={false} fontSize={12} />
            <YAxis dataKey="name" type="category" width={120} fontSize={12} />
            <Tooltip contentStyle={tooltipStyle} />
            <Bar dataKey="count" fill="hsl(var(--success))" radius={[0, 6, 6, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartCard>
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}

function ProviderIssues({ data }: { data: OpportunitySearchResponse }) {
  if (!data.provider_issues.length) return null;
  return (
    <Card>
      <CardContent className="space-y-2 p-4">
        {data.provider_issues.map((issue) => (
          <div key={`${issue.provider}-${issue.source}`} className="text-sm">
            <span className="font-medium">{issue.provider}</span> {issue.source}: {issue.message}
          </div>
        ))}
      </CardContent>
    </Card>
  );
}

function DiscoverySkeleton() {
  return (
    <div className="space-y-4">
      {Array.from({ length: 3 }).map((_, index) => (
        <Card key={index}>
          <CardContent className="space-y-4 p-6">
            <Skeleton className="h-6 w-2/3" />
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-20 w-full" />
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
