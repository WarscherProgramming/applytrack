import { Brand } from './brand';
import { NavLinks } from './nav-links';

/**
 * Desktop sidebar. Fixed width, full height, hidden below the lg breakpoint
 * (where the mobile drawer takes over instead).
 */
export function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r bg-card lg:flex">
      <div className="flex h-16 items-center border-b px-6">
        <Brand />
      </div>
      <div className="flex-1 overflow-y-auto p-4">
        <NavLinks />
      </div>
      <div className="border-t p-4">
        <p className="px-3 text-xs text-muted-foreground">v0.1.0 · Foundation</p>
      </div>
    </aside>
  );
}
