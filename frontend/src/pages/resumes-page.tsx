import { FileText } from 'lucide-react';

import type { DocumentConfig } from '@/features/documents/config';
import { DocumentLibrary } from '@/features/documents/components/document-library';
import { resumeHooks, resumesApi } from '@/features/resumes/resumes';

const RESUME_CONFIG: DocumentConfig = {
  api: resumesApi,
  hooks: resumeHooks,
  noun: 'resume',
  nounPlural: 'resumes',
  title: 'Resume Library',
  description: 'Upload, version, and manage the resumes you submit with applications.',
  icon: FileText,
};

export function ResumesPage() {
  return <DocumentLibrary config={RESUME_CONFIG} />;
}
