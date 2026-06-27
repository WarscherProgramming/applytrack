import type { DocumentGroup, DocumentItem } from './types';

/**
 * Group flat document records into logical documents keyed by name. The backend
 * already orders by name then version desc, but we sort defensively so grouping
 * is independent of fetch order. Each group exposes its latest version plus the
 * full version history (newest first).
 */
export function groupDocuments(items: DocumentItem[]): DocumentGroup[] {
  const byName = new Map<string, DocumentItem[]>();
  for (const item of items) {
    const bucket = byName.get(item.name);
    if (bucket) bucket.push(item);
    else byName.set(item.name, [item]);
  }

  const groups: DocumentGroup[] = [];
  for (const [name, versions] of byName) {
    versions.sort((a, b) => b.version - a.version);
    groups.push({ name, latest: versions[0], versions });
  }
  groups.sort((a, b) => a.name.localeCompare(b.name));
  return groups;
}

/** Human-friendly file extension label, e.g. "PDF". */
export function fileExtensionLabel(fileName: string): string {
  const dot = fileName.lastIndexOf('.');
  if (dot === -1 || dot === fileName.length - 1) return 'FILE';
  return fileName.slice(dot + 1).toUpperCase();
}

/**
 * Trigger a browser download for a document. The endpoint sets
 * Content-Disposition: attachment, so a transient anchor click saves the file
 * without navigating away.
 */
export function triggerDownload(url: string, fileName: string): void {
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = fileName;
  anchor.rel = 'noopener';
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
}
