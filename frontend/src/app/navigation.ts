import {
  Building2,
  CalendarClock,
  FileSignature,
  FileText,
  LayoutDashboard,
  GraduationCap,
  ListChecks,
  PenLine,
  Settings,
  Sparkles,
  UserSquare2,
  Briefcase,
  BrainCircuit,
  Bot,
  Compass,
  Radar,
  type LucideIcon,
} from 'lucide-react';

export interface NavItem {
  title: string;
  path: string;
  icon: LucideIcon;
}

/** Primary navigation, shared by the sidebar and the mobile drawer. */
export const NAV_ITEMS: NavItem[] = [
  { title: 'Career Copilot', path: '/', icon: Bot },
  { title: 'Dashboard', path: '/dashboard', icon: LayoutDashboard },
  { title: 'Companies', path: '/companies', icon: Building2 },
  { title: 'Applications', path: '/applications', icon: Briefcase },
  { title: 'Recruiters', path: '/recruiters', icon: UserSquare2 },
  { title: 'Resumes', path: '/resumes', icon: FileText },
  { title: 'Cover Letters', path: '/cover-letters', icon: FileSignature },
  { title: 'Resume Match', path: '/resume-match', icon: Sparkles },
  { title: 'AI Cover Letter', path: '/cover-letter-ai', icon: PenLine },
  { title: 'AI Interview Prep', path: '/interview-prep', icon: GraduationCap },
  { title: 'Career Intelligence', path: '/career-intelligence', icon: BrainCircuit },
  { title: 'Job Intelligence', path: '/job-intelligence', icon: Radar },
  { title: 'Opportunity Discovery', path: '/opportunity-discovery', icon: Compass },
  { title: 'Interviews', path: '/interviews', icon: CalendarClock },
  { title: 'Follow-ups', path: '/followups', icon: ListChecks },
  { title: 'Settings', path: '/settings', icon: Settings },
];
