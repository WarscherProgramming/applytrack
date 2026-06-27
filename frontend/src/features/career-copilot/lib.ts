import type { CareerCopilotResponse, CopilotPriority } from './types';

export function formatPercent(value: number | null) {
  return value === null ? 'No signal' : `${value.toFixed(1)}%`;
}

export function formatDateTime(value: string) {
  return new Intl.DateTimeFormat(undefined, {
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(new Date(value));
}

export function priorityVariant(priority: CopilotPriority) {
  if (priority === 'urgent') return 'destructive';
  if (priority === 'high') return 'warning';
  if (priority === 'medium') return 'secondary';
  return 'outline';
}

export function downloadDailyBriefing(data: CareerCopilotResponse) {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: 'application/json',
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `career-copilot-${data.generated_at.slice(0, 10)}.json`;
  link.click();
  URL.revokeObjectURL(url);
}

