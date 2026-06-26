import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

// NOTE: These charts use representative sample data. The backend does not yet
// expose time-series or per-status aggregation endpoints; wiring real data is a
// later milestone. The components are production-ready — only the data is stubbed.
const ACTIVITY_DATA = [
  { month: 'Jan', applications: 4 },
  { month: 'Feb', applications: 7 },
  { month: 'Mar', applications: 5 },
  { month: 'Apr', applications: 10 },
  { month: 'May', applications: 8 },
  { month: 'Jun', applications: 13 },
];

const STATUS_DATA = [
  { status: 'Applied', count: 12 },
  { status: 'Interview', count: 6 },
  { status: 'Offer', count: 2 },
  { status: 'Rejected', count: 5 },
  { status: 'Ghosted', count: 3 },
];

const BAR_COLORS = [
  'hsl(221.2 83.2% 53.3%)',
  'hsl(32.1 94.6% 43.7%)',
  'hsl(142.1 76.2% 36.3%)',
  'hsl(0 84.2% 60.2%)',
  'hsl(215.4 16.3% 46.9%)',
];

const tooltipStyle = {
  borderRadius: 8,
  border: '1px solid hsl(var(--border))',
  background: 'hsl(var(--popover))',
  color: 'hsl(var(--popover-foreground))',
  fontSize: 12,
};

export function DashboardCharts() {
  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Application activity</CardTitle>
          <CardDescription>
            Applications submitted per month · sample data
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={ACTIVITY_DATA} margin={{ left: -20, right: 8, top: 4 }}>
              <defs>
                <linearGradient id="activityFill" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="hsl(221.2 83.2% 53.3%)" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="hsl(221.2 83.2% 53.3%)" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              <XAxis dataKey="month" tickLine={false} axisLine={false} fontSize={12} stroke="hsl(var(--muted-foreground))" />
              <YAxis tickLine={false} axisLine={false} fontSize={12} stroke="hsl(var(--muted-foreground))" allowDecimals={false} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ stroke: 'hsl(var(--border))' }} />
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

      <Card>
        <CardHeader>
          <CardTitle>Applications by status</CardTitle>
          <CardDescription>Current pipeline breakdown · sample data</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={STATUS_DATA} margin={{ left: -20, right: 8, top: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              <XAxis dataKey="status" tickLine={false} axisLine={false} fontSize={12} stroke="hsl(var(--muted-foreground))" />
              <YAxis tickLine={false} axisLine={false} fontSize={12} stroke="hsl(var(--muted-foreground))" allowDecimals={false} />
              <Tooltip contentStyle={tooltipStyle} cursor={{ fill: 'hsl(var(--accent))', opacity: 0.4 }} />
              <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                {STATUS_DATA.map((_, index) => (
                  <Cell key={index} fill={BAR_COLORS[index % BAR_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
