import { useState, useEffect, useCallback } from 'react';

// Client-side "admin mode" flag, persisted in localStorage.
//
// NOTE: this is a UI-level role gate, not server-enforced security. Admin mode
// controls whether the Sessions tab shows the create-session controls; players
// without it can only join existing sessions and pick a side. Real enforcement
// (tying session creation to an authenticated admin account) comes later.
const STORAGE_KEY = 'btm.adminMode';

// Notify all hook instances in this tab when the value changes (the native
// 'storage' event only fires across tabs, not within the same one).
const EVENT = 'btm-admin-mode-change';

export function isAdminMode() {
  return localStorage.getItem(STORAGE_KEY) === 'true';
}

export function useAdminMode() {
  const [admin, setAdmin] = useState(isAdminMode);

  useEffect(() => {
    const sync = () => setAdmin(isAdminMode());
    window.addEventListener(EVENT, sync);
    window.addEventListener('storage', sync); // cross-tab
    return () => {
      window.removeEventListener(EVENT, sync);
      window.removeEventListener('storage', sync);
    };
  }, []);

  const setAdminMode = useCallback((value) => {
    localStorage.setItem(STORAGE_KEY, value ? 'true' : 'false');
    window.dispatchEvent(new Event(EVENT));
  }, []);

  return [admin, setAdminMode];
}
