import { ThemeToggle } from './theme-toggle';
import { UserMenu } from './user-menu';
import { MobileNav } from './mobile-nav';

/**
 * Top navigation bar. Sticky to the top of the content column. Holds the
 * mobile menu trigger (left, mobile only), and the theme toggle + user menu
 * (right). The page title comes from each page's own header.
 */
export function Topbar() {
  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between gap-4 border-b bg-background/80 px-4 backdrop-blur sm:px-6">
      <div className="flex items-center gap-2">
        <MobileNav />
      </div>
      <div className="flex items-center gap-1">
        <ThemeToggle />
        <UserMenu />
      </div>
    </header>
  );
}
