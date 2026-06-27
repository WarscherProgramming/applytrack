import { createDocumentApi } from '@/features/documents/api';
import { createDocumentHooks } from '@/features/documents/hooks';

/** Cover-letter document client + query hooks (shape shared with resumes). */
export const coverLettersApi = createDocumentApi('/cover-letters');
export const coverLetterHooks = createDocumentHooks(
  'cover-letters',
  coverLettersApi,
);
