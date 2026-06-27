import {
  Building2,
  CalendarClock,
  FileSignature,
  FileText,
  LayoutDashboard,
  ListChecks,
  Settings,
  UserSquare2,
  Briefcase,
  type LucideIcon,
} from 'lucide-react';

export interface NavItem {
  title: string;
  path: string;
  icon: LucideIcon;
}

/** Primary navigation, shared by the sidebar and the mobile drawer. */
export const NAV_ITEMS: NavItem[] = [
  { title: 'Dashboard', path: '/', icon: LayoutDashboard },
  { title: 'Companies', path: '/companies', icon: Building2 },
  { title: 'Applications', path: '/applications', icon: Briefcase },
  { title: 'Recruiters', path: '/recruiters', icon: UserSquare2 },
  { title: 'Resumes', path: '/resumes', icon: FileText },
  { title: 'Cover Letters', path: '/cover-letters', icon: FileSignature },
  { title: 'Interviews', path: '/interviews', icon: CalendarClock },
  { title: 'Follow-ups', path: '/followups', icon: ListChecks },
  { title: 'Settings', path: '/settings', icon: Settings },
];
