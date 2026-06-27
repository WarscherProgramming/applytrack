import type { BaseEntity, PaginationParams } from '@/types/api';

/**
 * A single stored document version (resume or cover letter). Mirrors the
 * backend DocumentResponse — resumes and cover letters share this shape.
 */
export interface DocumentItem extends BaseEntity {
  name: string;
  file_name: string;
  storage_path: string;
  version: number;
  notes: string | null;
}

export interface DocumentListParams extends PaginationParams {
  /** Case-insensitive match on document or file name. */
  query?: string;
  /** Restrict to a single logical document's versions. */
  name?: string;
}

/** Fields sent when uploading a new document (or new version). */
export interface DocumentUploadInput {
  file: File;
  /** Logical document name; defaults to the file's base name server-side. */
  name?: string;
  notes?: string;
}

/** Metadata-only edit (rename / notes). File content is immutable. */
export interface DocumentUpdateInput {
  name?: string;
  notes?: string | null;
}

/** A logical document grouped from its versions, newest first. */
export interface DocumentGroup {
  name: string;
  latest: DocumentItem;
  versions: DocumentItem[];
}
