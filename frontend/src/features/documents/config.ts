import type { LucideIcon } from 'lucide-react';

import type { DocumentApi } from './api';
import type { DocumentHooks } from './hooks';

/**
 * Everything the shared DocumentLibrary needs to render one resource. Resumes
 * and cover letters supply different copy, icon, API client, and query hooks
 * while reusing the same UI.
 */
export interface DocumentConfig {
  api: DocumentApi;
  hooks: DocumentHooks;
  /** Singular lower-case noun, e.g. "resume". */
  noun: string;
  /** Plural lower-case noun, e.g. "resumes". */
  nounPlural: string;
  title: string;
  description: string;
  icon: LucideIcon;
}
