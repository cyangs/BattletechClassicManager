import { useState, useEffect, useRef } from 'react';

import { API } from '../../api';

// Gear menu in the top-right corner. Currently holds the "Backup Database"
// action, which dumps the whole database to the shared seed file so a fresh
// `docker compose up` on another machine comes up pre-seeded.
export function SettingsMenu() {
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState(null); // { ok: bool, message: string }
  const ref = useRef(null);

  // Close the dropdown when clicking anywhere outside it.
  useEffect(() => {
    if (!open) return undefined;
    const onClick = (e) => {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    };
    document.addEventListener('mousedown', onClick);
    return () => document.removeEventListener('mousedown', onClick);
  }, [open]);

  const backup = () => {
    setBusy(true);
    setStatus(null);
    fetch(`${API}/api/admin/backup-database`, { method: 'POST' })
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.detail || 'Backup failed');
        const kb = Math.max(1, Math.round((body.size_bytes || 0) / 1024));
        setStatus({ ok: true, message: `Saved seed file (${kb} KB).` });
      })
      .catch((err) => setStatus({ ok: false, message: err.message }))
      .finally(() => setBusy(false));
  };

  return (
    <div className="relative ml-auto" ref={ref}>
      <button
        onClick={() => setOpen((v) => !v)}
        title="Settings"
        aria-label="Settings"
        className={`w-9 h-9 flex items-center justify-center rounded-md text-lg transition-colors ${
          open ? 'bg-gray-800 text-amber-400' : 'text-gray-400 hover:text-white hover:bg-gray-900'
        }`}
      >
        ⚙️
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-64 bg-gray-950 border border-gray-800 rounded-lg shadow-xl z-50 overflow-hidden">
          <button
            onClick={backup}
            disabled={busy}
            className="w-full flex items-center gap-2 px-4 py-3 text-left text-sm text-gray-200 hover:bg-gray-900 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <span>💾</span>
            {busy ? 'Backing up…' : 'Backup Database'}
          </button>
          {status && (
            <div
              className={`px-4 py-2 text-xs border-t border-gray-800 ${
                status.ok ? 'text-green-400' : 'text-red-400'
              }`}
            >
              {status.message}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
