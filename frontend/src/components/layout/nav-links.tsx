import { NavLink } from 'react-router-dom';

import { NAV_ITEMS } from '@/app/navigation';
import { cn } from '@/lib/utils';

interface NavLinksProps {
  /** Called after a link is clicked — used to close the mobile drawer. */
  onNavigate?: () => void;
}

/** The list of primary navigation links, shared between sidebar and drawer. */
export function NavLinks({ onNavigate }: NavLinksProps) {
  return (
    <nav className="flex flex-col gap-1" aria-label="Primary">
      {NAV_ITEMS.map(({ title, path, icon: Icon }) => (
        <NavLink
          key={path}
          to={path}
          // `end` on the dashboard root so it isn't marked active on every route.
          end={path === '/'}
          onClick={onNavigate}
          className={({ isActive }) =>
            cn(
              'flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring',
              isActive
                ? 'bg-primary/10 text-primary'
                : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground',
            )
          }
        >
          <Icon className="h-4 w-4 shrink-0" />
          {title}
        </NavLink>
      ))}
    </nav>
  );
}
