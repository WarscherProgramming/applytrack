import { createBrowserRouter } from 'react-router-dom';

import { AppLayout } from '@/layouts/app-layout';
import { ApplicationsPage } from '@/pages/applications-page';
import { CompaniesPage } from '@/pages/companies-page';
import { DashboardPage } from '@/pages/dashboard-page';
import { FollowupsPage } from '@/pages/followups-page';
import { InterviewsPage } from '@/pages/interviews-page';
import { NotFoundPage } from '@/pages/not-found-page';
import { RecruitersPage } from '@/pages/recruiters-page';
import { SettingsPage } from '@/pages/settings-page';

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
      { path: 'interviews', element: <InterviewsPage /> },
      { path: 'followups', element: <FollowupsPage /> },
      { path: 'settings', element: <SettingsPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);
