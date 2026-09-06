import { useState, useEffect, useCallback } from 'react';

import { API } from '../../api';
import MechsLibrary from '../mechs/MechsLibrary';
import WeaponsLibrary from '../weapons/WeaponsLibrary';
import Sessions from '../sessions/Sessions';
import { SettingsMenu } from './SettingsMenu';

const TABS = [
  { id: 'mechs', label: '🤖 Mechs Library' },
  { id: 'weapons', label: '⚔️ Weapons & Parts Library' },
  { id: 'sessions', label: '🎲 Sessions' },
];

// =====================================================================
// ROOT: top-level tab shell shared across the three libraries
// =====================================================================
export default function MechDashboard() {
  const [tab, setTab] = useState('mechs');
  const [mechs, setMechs] = useState([]);
  const [weapons, setWeapons] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const loadMechs = useCallback(
    () => fetch(`${API}/api/mechs`).then((r) => r.json()).then(setMechs),
    [],
  );
  const loadWeapons = useCallback(
    () => fetch(`${API}/api/weapons`).then((r) => r.json()).then(setWeapons),
    [],
  );
  const loadSessions = useCallback(
    () => fetch(`${API}/api/sessions`).then((r) => r.json()).then(setSessions),
    [],
  );

  useEffect(() => {
    Promise.all([loadMechs(), loadWeapons(), loadSessions()])
      .catch((err) => setError(String(err)))
      .finally(() => setLoading(false));
  }, [loadMechs, loadWeapons, loadSessions]);

  return (
    <div className="flex flex-col h-screen bg-gray-900 text-gray-100 font-sans">
      {/* TOP NAVIGATION BAR */}
      <header className="flex items-center gap-8 px-6 h-16 bg-gray-950 border-b border-gray-800 shrink-0">
        <div className="text-lg font-bold text-amber-500 whitespace-nowrap">
          Calvin's Super Awesome BattleTech Campaign Manager Beta Version 1.0
        </div>
        <nav className="flex gap-1">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                tab === t.id
                  ? 'bg-amber-950/40 text-amber-400 border border-amber-700/50'
                  : 'text-gray-400 hover:text-white hover:bg-gray-900'
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>

        <SettingsMenu />
      </header>

      {/* ACTIVE TAB BODY */}
      <main className="flex-1 overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-400">Loading BattleMech Systems...</div>
        ) : error ? (
          <div className="p-8 text-center text-red-400">
            Could not reach the FastAPI backend at {API}.<br />
            <span className="text-xs text-gray-500">{error}</span>
          </div>
        ) : (
          <>
            {tab === 'mechs' && (
              <MechsLibrary mechs={mechs} weapons={weapons} reload={loadMechs} />
            )}
            {tab === 'weapons' && <WeaponsLibrary weapons={weapons} reload={loadWeapons} />}
            {tab === 'sessions' && (
              <Sessions sessions={sessions} mechs={mechs} reload={loadSessions} />
            )}
          </>
        )}
      </main>
    </div>
  );
}
