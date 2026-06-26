import { useEffect, useRef } from 'react';

type HotkeyHandler = (event: KeyboardEvent) => void;
type HotkeyMap = Record<string, HotkeyHandler>;

/**
 * Register global keyboard shortcuts.
 *
 * Keys are matched against `KeyboardEvent.key`. Shortcuts are ignored while the
 * user is typing in a form field (input/textarea/select/contenteditable) or
 * holding a modifier, so they never hijack normal typing. Handlers are read
 * from a ref so the window listener is attached only once.
 */
export function useHotkeys(map: HotkeyMap, enabled = true): void {
  const mapRef = useRef(map);
  mapRef.current = map;

  useEffect(() => {
    if (!enabled) return;

    function onKeyDown(event: KeyboardEvent) {
      if (event.ctrlKey || event.metaKey || event.altKey) return;

      const target = event.target as HTMLElement | null;
      const tag = target?.tagName;
      const isEditable =
        tag === 'INPUT' ||
        tag === 'TEXTAREA' ||
        tag === 'SELECT' ||
        Boolean(target?.isContentEditable);
      if (isEditable) return;

      const handler = mapRef.current[event.key];
      if (handler) handler(event);
    }

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [enabled]);
}
