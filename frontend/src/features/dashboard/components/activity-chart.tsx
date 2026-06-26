import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { Badge } from '@/components/ui/badge';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

// Placeholder: the backend has no time-series aggregation endpoint yet, so this
// trend uses representative sample data. The chart is production-ready; only the
// data source is stubbed (clearly labelled below and via the "Sample" badge).
const ACTIVITY_DATA = [
  { month: 'Jan', applications: 4 },
  { month: 'Feb', applications: 7 },
  { month: 'Mar', applications: 5 },
  { month: 'Apr', applications: 10 },
  { month: 'May', applications: 8 },
  { month: 'Jun', applications: 13 },
];

const tooltipStyle = {
  borderRadius: 8,
  border: '1px solid hsl(var(--border))',
  background: 'hsl(var(--popover))',
  color: 'hsl(var(--popover-foreground))',
  fontSize: 12,
};

export function ActivityChart() {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Application activity</CardTitle>
          <Badge variant="secondary">Sample data</Badge>
        </div>
        <CardDescription>
          Applications submitted per month · placeholder until aggregation lands
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart
            data={ACTIVITY_DATA}
            margin={{ left: -20, right: 8, top: 4 }}
          >
            <defs>
              <linearGradient id="activityFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(221.2 83.2% 53.3%)" stopOpacity={0.4} />
                <stop offset="95%" stopColor="hsl(221.2 83.2% 53.3%)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid
              strokeDasharray="3 3"
              stroke="hsl(var(--border))"
              vertical={false}
            />
            <XAxis
              dataKey="month"
              tickLine={false}
              axisLine={false}
              fontSize={12}
              stroke="hsl(var(--muted-foreground))"
            />
            <YAxis
              tickLine={false}
              axisLine={false}
              fontSize={12}
              stroke="hsl(var(--muted-foreground))"
              allowDecimals={false}
            />
            <Tooltip
              contentStyle={tooltipStyle}
              cursor={{ stroke: 'hsl(var(--border))' }}
            />
            <Area
              type="monotone"
              dataKey="applications"
              stroke="hsl(221.2 83.2% 53.3%)"
              strokeWidth={2}
              fill="url(#activityFill)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
