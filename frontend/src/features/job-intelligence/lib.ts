import type { JobIntelligenceParams, JobIntelligenceResponse } from './types';

export function compactParams(params: object): JobIntelligenceParams {
  return Object.fromEntries(
    Object.entries(params).filter(
      ([, value]) => typeof value === 'string' && value.trim().length > 0,
    ),
  ) as JobIntelligenceParams;
}

export function formatPercent(value: number | null) {
  return value === null ? 'No signal' : `${value.toFixed(1)}%`;
}

export function downloadJobIntelligence(data: JobIntelligenceResponse) {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: 'application/json',
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `job-intelligence-${data.generated_at.slice(0, 10)}.json`;
  link.click();
  URL.revokeObjectURL(url);
}
