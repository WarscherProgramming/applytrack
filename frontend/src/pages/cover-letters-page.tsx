import { FileSignature } from 'lucide-react';

import { coverLetterHooks, coverLettersApi } from '@/features/cover-letters/cover-letters';
import type { DocumentConfig } from '@/features/documents/config';
import { DocumentLibrary } from '@/features/documents/components/document-library';

const COVER_LETTER_CONFIG: DocumentConfig = {
  api: coverLettersApi,
  hooks: coverLetterHooks,
  noun: 'cover letter',
  nounPlural: 'cover letters',
  title: 'Cover Letter Library',
  description:
    'Upload, version, and manage the cover letters you submit with applications.',
  icon: FileSignature,
};

export function CoverLettersPage() {
  return <DocumentLibrary config={COVER_LETTER_CONFIG} />;
}
