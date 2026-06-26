import { useQuery } from '@tanstack/react-query';
import { useMemo } from 'react';

import type { Recruiter } from '../types/recruiter.types';
import { recruitersApi } from '../api/recruiters.api';

const EMPTY: Recruiter[] = [];

/** Best display label for a recruiter (full name, else email). */
export function recruiterDisplayName(r: Recruiter): string {
  return [r.first_name, r.last_name].filter(Boolean).join(' ') || r.email || 'Recruiter';
}

/**
 * Loads recruiters for selection + id→name lookup. Used by the interview form's
 * recruiter picker and the calendar to label interviews with their recruiter.
 */
export function useRecruiterOptions() {
  const query = useQuery({
    queryKey: ['recruiters', 'options'],
    queryFn: () => recruitersApi.list({ skip: 0, limit: 100 }),
  });

  const options = query.data?.items ?? EMPTY;

  const byId = useMemo(() => {
    const map = new Map<string, string>();
    for (const recruiter of query.data?.items ?? []) {
      map.set(recruiter.id, recruiterDisplayName(recruiter));
    }
    return map;
  }, [query.data]);

  return { ...query, options, byId };
}
