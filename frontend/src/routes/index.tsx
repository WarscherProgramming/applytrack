import { lazy } from 'react';
import { createBrowserRouter } from 'react-router-dom';

import { AppLayout } from '@/layouts/app-layout';

// Each page is code-split into its own chunk so the initial bundle only carries
// the shell + the first route. Pages use named exports, so we map them to the
// `default` shape React.lazy expects. The Suspense boundary lives in AppLayout
// around the Outlet, so a single fallback covers every lazy route.
const DashboardPage = lazy(() =>
  import('@/pages/dashboard-page').then((m) => ({ default: m.DashboardPage })),
);
const CompaniesPage = lazy(() =>
  import('@/pages/companies-page').then((m) => ({ default: m.CompaniesPage })),
);
const ApplicationsPage = lazy(() =>
  import('@/pages/applications-page').then((m) => ({
    default: m.ApplicationsPage,
  })),
);
const RecruitersPage = lazy(() =>
  import('@/pages/recruiters-page').then((m) => ({ default: m.RecruitersPage })),
);
const ResumesPage = lazy(() =>
  import('@/pages/resumes-page').then((m) => ({ default: m.ResumesPage })),
);
const CoverLettersPage = lazy(() =>
  import('@/pages/cover-letters-page').then((m) => ({
    default: m.CoverLettersPage,
  })),
);
const ResumeMatchPage = lazy(() =>
  import('@/pages/resume-match-page').then((m) => ({
    default: m.ResumeMatchPage,
  })),
);
const InterviewsPage = lazy(() =>
  import('@/pages/interviews-page').then((m) => ({ default: m.InterviewsPage })),
);
const FollowupsPage = lazy(() =>
  import('@/pages/followups-page').then((m) => ({ default: m.FollowupsPage })),
);
const SettingsPage = lazy(() =>
  import('@/pages/settings-page').then((m) => ({ default: m.SettingsPage })),
);
const NotFoundPage = lazy(() =>
  import('@/pages/not-found-page').then((m) => ({ default: m.NotFoundPage })),
);

/**
 * Application routes. A single layout route renders the shell (sidebar +
 * topbar) and nests every page via <Outlet />. A catch-all renders the 404.
 */
export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: 'companies', element: <CompaniesPage /> },
      { path: 'applications', element: <ApplicationsPage /> },
      { path: 'recruiters', element: <RecruitersPage /> },
      { path: 'resumes', element: <ResumesPage /> },
      { path: 'cover-letters', element: <CoverLettersPage /> },
      { path: 'resume-match', element: <ResumeMatchPage /> },
      { path: 'interviews', element: <InterviewsPage /> },
      { path: 'followups', element: <FollowupsPage /> },
      { path: 'settings', element: <SettingsPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);
