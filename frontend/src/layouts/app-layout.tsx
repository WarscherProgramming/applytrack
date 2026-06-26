import { Suspense } from 'react';
import { Outlet } from 'react-router-dom';

import { PageFallback } from '@/components/common/page-fallback';
import { Sidebar } from '@/components/layout/sidebar';
import { Topbar } from '@/components/layout/topbar';

/**
 * The application shell: persistent sidebar (desktop) + sticky topbar, with the
 * active route rendered into the scrollable main content area. Used as the
 * layout route wrapping every page.
 *
 * The Outlet is wrapped in a single Suspense boundary so lazily-loaded page
 * chunks show the fallback only in the content area — the sidebar and topbar
 * stay mounted across route transitions.
 */
export function AppLayout() {
  return (
    <div className="flex h-full min-h-screen bg-background">
      <Sidebar />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar />
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
            <Suspense fallback={<PageFallback />}>
              <Outlet />
            </Suspense>
          </div>
        </main>
      </div>
    </div>
  );
}
