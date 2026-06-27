import { Clock, Coins, Cpu, Hash } from 'lucide-react';

import type { UsageSummary as UsageSummaryData } from '../types';

interface UsageSummaryProps {
  usage: UsageSummaryData;
}

function Stat({
  icon: Icon,
  label,
  value,
}: {
  icon: typeof Hash;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <Icon className="h-4 w-4 text-muted-foreground" />
      <span className="text-muted-foreground">{label}:</span>
      <span className="font-medium tabular-nums">{value}</span>
    </div>
  );
}

/** Compact token/cost/latency summary for a generation. */
export function UsageSummary({ usage }: UsageSummaryProps) {
  const cost =
    usage.estimated_cost_usd != null
      ? `$${usage.estimated_cost_usd.toFixed(4)}`
      : '—';

  return (
    <div className="flex flex-wrap gap-x-5 gap-y-2 rounded-lg border bg-muted/30 px-4 py-3 text-xs">
      <Stat icon={Cpu} label="Model" value={`${usage.provider}/${usage.model}`} />
      <Stat
        icon={Hash}
        label="Tokens"
        value={`${usage.total_tokens.toLocaleString()} (${usage.prompt_tokens.toLocaleString()} in / ${usage.completion_tokens.toLocaleString()} out)`}
      />
      <Stat icon={Coins} label="Est. cost" value={cost} />
      <Stat icon={Clock} label="Latency" value={`${usage.latency_ms} ms`} />
    </div>
  );
}
