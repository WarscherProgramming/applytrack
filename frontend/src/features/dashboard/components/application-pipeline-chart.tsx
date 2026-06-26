import { Layers } from 'lucide-react';
import { useMemo } from 'react';
import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { EmptyState } from '@/components/common/empty-state';
import { ErrorState } from '@/components/common/error-state';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';

import { useApplicationsIndex } from '../hooks/use-applications-index';
import { buildPipelineData } from '../lib/application-pipeline';

const tooltipStyle = {
  borderRadius: 8,
  border: '1px solid hsl(var(--border))',
  background: 'hsl(var(--popover))',
  color: 'hsl(var(--popover-foreground))',
  fontSize: 12,
};

/**
 * Real per-status breakdown of the application pipeline, derived from the
 * cached applications index. Horizontal bars keep the stage labels readable.
 */
export function ApplicationPipelineChart() {
  const { statusCounts, isLoading, isError, error, refetch } =
    useApplicationsIndex();

  const data = useMemo(
    () => buildPipelineData(statusCounts),
    [statusCounts],
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Application pipeline</CardTitle>
        <CardDescription>Applications by current status · live data</CardDescription>
      </CardHeader>
      <CardContent>
        {isError ? (
          <ErrorState error={error} onRetry={refetch} className="py-8" />
        ) : isLoading ? (
          <Skeleton className="h-[260px] w-full" />
        ) : data.length === 0 ? (
          <EmptyState
            icon={Layers}
            title="No applications yet"
            description="Your pipeline breakdown will appear here once you add applications."
            className="border-0 py-10"
          />
        ) : (
          <ResponsiveContainer width="100%" height={Math.max(220, data.length * 44)}>
            <BarChart
              data={data}
              layout="vertical"
              margin={{ left: 12, right: 16, top: 4, bottom: 4 }}
            >
              <XAxis
                type="number"
                allowDecimals={false}
                tickLine={false}
                axisLine={false}
                fontSize={12}
                stroke="hsl(var(--muted-foreground))"
              />
              <YAxis
                type="category"
                dataKey="label"
                width={110}
                tickLine={false}
                axisLine={false}
                fontSize={12}
                stroke="hsl(var(--muted-foreground))"
              />
              <Tooltip
                contentStyle={tooltipStyle}
                cursor={{ fill: 'hsl(var(--accent))', opacity: 0.4 }}
              />
              <Bar dataKey="count" radius={[0, 6, 6, 0]} barSize={22}>
                {data.map((datum) => (
                  <Cell key={datum.status} fill={datum.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
