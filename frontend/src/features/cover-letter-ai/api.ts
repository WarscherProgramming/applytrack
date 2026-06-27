import { apiClient } from '@/services/api-client';

import type {
  CoverLetterGenerateInput,
  CoverLetterGenerateResponse,
  CoverLetterSaveInput,
  CoverLetterVersionContent,
  SavedCoverLetter,
} from './types';

/** Typed wrappers around the /cover-letter-ai endpoints. */
export const coverLetterAiApi = {
  generate(
    input: CoverLetterGenerateInput,
  ): Promise<CoverLetterGenerateResponse> {
    return apiClient
      .post<CoverLetterGenerateResponse>('/cover-letter-ai/generate', input)
      .then((res) => res.data);
  },

  save(input: CoverLetterSaveInput): Promise<SavedCoverLetter> {
    return apiClient
      .post<SavedCoverLetter>('/cover-letter-ai/save', input)
      .then((res) => res.data);
  },

  versions(name: string): Promise<CoverLetterVersionContent[]> {
    return apiClient
      .get<{ items: CoverLetterVersionContent[] }>('/cover-letter-ai/versions', {
        params: { name },
      })
      .then((res) => res.data.items);
  },
};
