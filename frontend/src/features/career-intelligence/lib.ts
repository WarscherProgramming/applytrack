import type { CareerIntelligenceResponse } from './types';

export function formatPercent(value: number | null) {
  return value === null ? 'Not enough data' : `${value.toFixed(1)}%`;
}

export function formatNumber(value: number | null) {
  return value === null ? 'Not enough data' : value.toLocaleString();
}

export function compactParams<T extends object>(params: T) {
  return Object.fromEntries(
    Object.entries(params).filter(
      ([, value]) => typeof value === 'string' && value.trim().length > 0,
    ),
  );
}

export function downloadCareerIntelligence(data: CareerIntelligenceResponse) {
  const blob = new Blob([JSON.stringify(data, null, 2)], {
    type: 'application/json',
  });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `career-intelligence-${data.generated_at.slice(0, 10)}.json`;
  link.click();
  URL.revokeObjectURL(url);
}
