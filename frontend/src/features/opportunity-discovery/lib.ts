import type { JobProviderName, OpportunitySearchRequest, WorkMode } from './types';

export interface OpportunityDiscoveryFilters {
  query: string;
  greenhouse_boards: string;
  lever_companies: string;
  ashby_boards: string;
  rss_feeds: string;
  providers: JobProviderName[];
  remote: 'any' | WorkMode;
  location: string;
  min_salary: string;
  technologies: string;
  preferred_location: string;
  preferred_job_type: string;
  preferred_industry: string;
  limit: string;
}

export function buildSearchRequest(
  filters: OpportunityDiscoveryFilters,
): OpportunitySearchRequest {
  return {
    query: clean(filters.query),
    providers: filters.providers,
    greenhouse_boards: csv(filters.greenhouse_boards),
    lever_companies: csv(filters.lever_companies),
    ashby_boards: csv(filters.ashby_boards),
    rss_feeds: csv(filters.rss_feeds),
    remote: filters.remote === 'any' ? null : filters.remote,
    location: clean(filters.location),
    min_salary: numberOrNull(filters.min_salary),
    technologies: csv(filters.technologies),
    preferred_location: clean(filters.preferred_location),
    preferred_job_type: clean(filters.preferred_job_type),
    preferred_industry: clean(filters.preferred_industry),
    limit: numberOrNull(filters.limit) ?? 25,
  };
}

export function toggleProvider(
  providers: JobProviderName[],
  provider: JobProviderName,
) {
  return providers.includes(provider)
    ? providers.filter((item) => item !== provider)
    : [...providers, provider];
}

function csv(value: string) {
  return value
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);
}

function clean(value: string) {
  const trimmed = value.trim();
  return trimmed.length ? trimmed : null;
}

function numberOrNull(value: string) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}
