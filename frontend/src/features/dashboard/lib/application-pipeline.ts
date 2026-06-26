import type { ApplicationStatus } from '@/features/applications/types/application.types';
import { humanizeEnum } from '@/utils/format';

export interface PipelineDatum {
  status: ApplicationStatus;
  label: string;
  count: number;
  color: string;
}

// Concrete HSL values (not CSS vars) because Recharts writes them to SVG fill
// attributes, which don't resolve `var(--…)`. Colours mirror the semantic
// palette used by StatusBadge so the chart and badges stay visually consistent.
const NEUTRAL = 'hsl(215.4 16.3% 56%)';
const PRIMARY = 'hsl(221.2 83.2% 53.3%)';
const WARNING = 'hsl(32.1 94.6% 43.7%)';
const SUCCESS = 'hsl(142.1 71% 45%)';
const DESTRUCTIVE = 'hsl(0 72% 51%)';

// Canonical funnel order with each stage's colour.
const PIPELINE_ORDER: { status: ApplicationStatus; color: string }[] = [
  { status: 'draft', color: NEUTRAL },
  { status: 'applied', color: PRIMARY },
  { status: 'assessment', color: WARNING },
  { status: 'phone_screen', color: WARNING },
  { status: 'interview', color: WARNING },
  { status: 'final_interview', color: WARNING },
  { status: 'offer', color: SUCCESS },
  { status: 'accepted', color: SUCCESS },
  { status: 'rejected', color: DESTRUCTIVE },
  { status: 'withdrawn', color: NEUTRAL },
  { status: 'ghosted', color: NEUTRAL },
];

/**
 * Turn raw per-status counts into ordered chart rows. Empty stages are dropped
 * so the chart shows only the stages actually in play.
 */
export function buildPipelineData(
  statusCounts: Map<ApplicationStatus, number>,
): PipelineDatum[] {
  return PIPELINE_ORDER.map(({ status, color }) => ({
    status,
    label: humanizeEnum(status),
    count: statusCounts.get(status) ?? 0,
    color,
  })).filter((d) => d.count > 0);
}
