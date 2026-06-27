import { createDocumentApi } from '@/features/documents/api';
import { createDocumentHooks } from '@/features/documents/hooks';

/** Resume document client + query hooks (shape shared with cover letters). */
export const resumesApi = createDocumentApi('/resumes');
export const resumeHooks = createDocumentHooks('resumes', resumesApi);
