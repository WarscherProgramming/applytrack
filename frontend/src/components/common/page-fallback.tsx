import { LoadingSpinner } from './loading-spinner';

/**
 * Suspense fallback for lazily-loaded route chunks. Fills the content area
 * (the app shell stays mounted around it) and centres a spinner so route
 * transitions feel intentional rather than blank.
 */
export function PageFallback() {
  return (
    <div className="flex min-h-[60vh] items-center justify-center">
      <LoadingSpinner label="Loading…" />
    </div>
  );
}
