import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { coverLetterHooks } from '@/features/cover-letters/cover-letters';

import { coverLetterAiApi } from './api';
import type { CoverLetterGenerateInput, CoverLetterSaveInput } from './types';

export const coverLetterAiKeys = {
  all: ['cover-letter-ai'] as const,
  versions: (name: string) => [...coverLetterAiKeys.all, 'versions', name] as const,
};

export function useGenerateCoverLetter() {
  return useMutation({
    mutationFn: (input: CoverLetterGenerateInput) =>
      coverLetterAiApi.generate(input),
  });
}

export function useSaveCoverLetter() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CoverLetterSaveInput) => coverLetterAiApi.save(input),
    onSuccess: (saved) => {
      // The saved version lands in the Cover Letter Library — refresh its caches
      // (list, options) and this letter's version history.
      queryClient.invalidateQueries({ queryKey: coverLetterHooks.keys.all });
      queryClient.invalidateQueries({
        queryKey: coverLetterAiKeys.versions(saved.name),
      });
    },
  });
}

export function useCoverLetterVersions(name: string | null) {
  return useQuery({
    queryKey: coverLetterAiKeys.versions(name ?? 'none'),
    queryFn: () => coverLetterAiApi.versions(name as string),
    enabled: Boolean(name),
  });
}
