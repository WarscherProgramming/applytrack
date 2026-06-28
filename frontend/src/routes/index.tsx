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
const CareerCopilotPage = lazy(() =>
  import('@/pages/career-copilot-page').then((m) => ({
    default: m.CareerCopilotPage,
  })),
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
const CoverLetterAIPage = lazy(() =>
  import('@/pages/cover-letter-ai-page').then((m) => ({
    default: m.CoverLetterAIPage,
  })),
);
const InterviewPrepPage = lazy(() =>
  import('@/pages/interview-prep-page').then((m) => ({
    default: m.InterviewPrepPage,
  })),
);
const CareerIntelligencePage = lazy(() =>
  import('@/pages/career-intelligence-page').then((m) => ({
    default: m.CareerIntelligencePage,
  })),
);
const JobIntelligencePage = lazy(() =>
  import('@/pages/job-intelligence-page').then((m) => ({
    default: m.JobIntelligencePage,
  })),
);
const OpportunityDiscoveryPage = lazy(() =>
  import('@/pages/opportunity-discovery-page').then((m) => ({
    default: m.OpportunityDiscoveryPage,
  })),
);
const DailyBriefingPage = lazy(() =>
  import('@/pages/daily-briefing-page').then((m) => ({
    default: m.DailyBriefingPage,
  })),
);
const CalendarIntegrationPage = lazy(() =>
  import('@/pages/calendar-integration-page').then((m) => ({
    default: m.CalendarIntegrationPage,
  })),
);
const TasksPage = lazy(() =>
  import('@/pages/tasks-page').then((m) => ({ default: m.TasksPage })),
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
      { index: true, element: <CareerCopilotPage /> },
      { path: 'dashboard', element: <DashboardPage /> },
      { path: 'companies', element: <CompaniesPage /> },
      { path: 'applications', element: <ApplicationsPage /> },
      { path: 'recruiters', element: <RecruitersPage /> },
      { path: 'resumes', element: <ResumesPage /> },
      { path: 'cover-letters', element: <CoverLettersPage /> },
      { path: 'resume-match', element: <ResumeMatchPage /> },
      { path: 'cover-letter-ai', element: <CoverLetterAIPage /> },
      { path: 'interview-prep', element: <InterviewPrepPage /> },
      { path: 'career-intelligence', element: <CareerIntelligencePage /> },
      { path: 'job-intelligence', element: <JobIntelligencePage /> },
      { path: 'opportunity-discovery', element: <OpportunityDiscoveryPage /> },
      { path: 'daily-briefing', element: <DailyBriefingPage /> },
      { path: 'tasks', element: <TasksPage /> },
      { path: 'settings/calendar', element: <CalendarIntegrationPage /> },
      { path: 'interviews', element: <InterviewsPage /> },
      { path: 'followups', element: <FollowupsPage /> },
      { path: 'settings', element: <SettingsPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);
