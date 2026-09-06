import { useState } from 'react';

import { API } from '../../api';
import { COLOR_PALETTE } from '../../lib/palette';
import { TeamBadge } from '../../components/badges';
import { SessionMechRow } from './SessionMechRow';
import { SessionHistory } from './SessionHistory';

// =====================================================================
// TAB 3: SESSIONS — game rooms with deployed mech rosters
// =====================================================================
export default function Sessions({ sessions, mechs, reload }) {
  const [selectedId, setSelectedId] = useState(sessions[0]?.id ?? null);
  const [newName, setNewName] = useState('');
  const [mechToAdd, setMechToAdd] = useState('');
  const [addTeam, setAddTeam] = useState('player');
  const [pilotName, setPilotName] = useState('');
  const [pilotGunnery, setPilotGunnery] = useState('4');
  const [deployColor, setDeployColor] = useState('none');
  const [detailView, setDetailView] = useState('combat'); // 'combat' | 'history'
  const [expandedUnits, setExpandedUnits] = useState(() => new Set());

  const toggleUnit = (id) =>
    setExpandedUnits((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const selected = sessions.find((s) => s.id === selectedId) ?? null;

  const createSession = (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    fetch(`${API}/api/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: newName.trim() }),
    })
      .then((r) => r.json())
      .then((created) => {
        setNewName('');
        reload().then(() => setSelectedId(created.id));
      })
      .catch((err) => alert('Error creating session: ' + err));
  };

  const deleteSession = (id) => {
    if (!confirm('Delete this game session?')) return;
    fetch(`${API}/api/sessions/${id}`, { method: 'DELETE' })
      .then(() => {
        if (selectedId === id) setSelectedId(null);
        reload();
      })
      .catch((err) => alert('Error deleting session: ' + err));
  };

  const addMech = () => {
    if (!mechToAdd || !selected) return;
    fetch(`${API}/api/sessions/${selected.id}/mechs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mech_ids: [parseInt(mechToAdd, 10)],
        team: addTeam,
        pilot_name: pilotName.trim() || null,
        pilot_gunnery_skill: parseInt(pilotGunnery, 10),
        accent_color: deployColor === 'none' ? null : deployColor,
      }),
    })
      .then(() => {
        setMechToAdd('');
        setPilotName('');
        setPilotGunnery('4');
        setDeployColor('none');
        reload();
      })
      .catch((err) => alert('Error adding mech: ' + err));
  };

  const addEnemy = (mechId) => {
    if (!mechId || !selected) return;
    fetch(`${API}/api/sessions/${selected.id}/mechs`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mech_ids: [parseInt(mechId, 10)], team: 'enemy' }),
    })
      .then(() => reload())
      .catch((err) => alert('Error adding enemy: ' + err));
  };

  const removeUnit = (unitId) => {
    fetch(`${API}/api/sessions/${selected.id}/mechs/${unitId}`, { method: 'DELETE' })
      .then(() => reload())
      .catch((err) => alert('Error removing mech: ' + err));
  };

  const postAction = (path, errLabel) =>
    fetch(`${API}/api/sessions/${selected.id}/${path}`, { method: 'POST' })
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.detail || `${errLabel} failed`);
        reload();
      })
      .catch((err) => alert(`Error: ${err.message}`));

  const startSession = () => postAction('start', 'Start');
  const runTurn = () => postAction('turn', 'Run turn');
  const endSession = () => {
    if (!confirm('End this session? Turns and weapon fire will be locked and it becomes read-only.'))
      return;
    postAction('end', 'End');
  };

  const inProgress = selected?.status === 'in_progress';
  const completed = selected?.status === 'completed';
  const playerUnits = selected ? selected.mechs.filter((u) => u.team !== 'enemy') : [];
  const enemyUnits = selected ? selected.mechs.filter((u) => u.team === 'enemy') : [];

  return (
    <div className="flex h-full">
      {/* LEFT: session list + create */}
      <div className="w-80 border-r border-gray-800 bg-gray-950 flex flex-col shrink-0">
        <div className="p-4 border-b border-gray-800">
          <h1 className="text-lg font-bold text-amber-500 mb-3">Game Sessions</h1>
          <form onSubmit={createSession} className="space-y-2">
            <input
              type="text"
              placeholder="New session name..."
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-sm text-white focus:outline-none focus:border-amber-500"
            />
            <button
              type="submit"
              disabled={!newName.trim()}
              className="w-full px-3 py-2 bg-amber-600 hover:bg-amber-700 rounded text-white text-sm font-bold disabled:opacity-40 disabled:cursor-not-allowed"
            >
              + Create Session
            </button>
          </form>

          {/* Add enemy chassis to the currently selected session. */}
          <div className="mt-3">
            <label className="block text-[10px] uppercase tracking-wider text-red-400/80 mb-1">
              Add Enemy Forces to Current Session
            </label>
            <select
              value=""
              disabled={!selected || completed}
              onChange={(e) => {
                if (e.target.value) addEnemy(e.target.value);
              }}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-red-500 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              <option value="">
                {selected ? '+ Add enemy chassis…' : 'Select a session first…'}
              </option>
              {mechs.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.name} {m.model} - ({m.tonnage}t)
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => {
                setSelectedId(s.id);
                setDetailView('combat');
              }}
              className={`w-full text-left p-4 border-b border-gray-800 transition-colors flex justify-between items-center ${
                selectedId === s.id
                  ? 'bg-amber-950/40 border-l-4 border-l-amber-500'
                  : 'hover:bg-gray-900'
              }`}
            >
              <div>
                <div className="font-semibold text-white">{s.name}</div>
                <div className="text-xs text-gray-500 mt-0.5">
                  {s.mechs.length} mech(s)
                  {s.status === 'in_progress' && ` · Turn ${s.current_turn}`}
                </div>
                <div className="text-xs text-gray-600 mt-0.5">
                  {new Date(s.created_on).toLocaleString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    year: 'numeric',
                    hour: 'numeric',
                    minute: '2-digit',
                  })}
                </div>
              </div>
              <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-gray-800 border border-gray-700 text-amber-400">
                {s.status}
              </span>
            </button>
          ))}
          {sessions.length === 0 && (
            <div className="p-4 text-center text-xs text-gray-500">
              No sessions yet. Create one above.
            </div>
          )}
        </div>
      </div>

      {/* RIGHT: session detail */}
      <div className="flex-1 flex flex-col bg-gray-900 overflow-hidden">
        {selected ? (
          <>
            {/* Header + action bar */}
            <div className="p-6 bg-gray-950 border-b border-gray-800 flex justify-between items-center">
              <div>
                <h2 className="text-3xl font-extrabold text-white">{selected.name}</h2>
                <p className="text-gray-400 text-xs mt-1 font-mono uppercase">
                  Status: {selected.status}
                  {inProgress && ` · Turn ${selected.current_turn}`} · {selected.mechs.length} unit(s)
                </p>
              </div>
              <div className="flex items-center gap-3">
                {completed ? (
                  <span className="px-3 py-1.5 rounded bg-gray-800 border border-gray-700 text-gray-300 text-xs uppercase font-bold tracking-wider">
                    ✔ Session Completed
                  </span>
                ) : (
                  <>
                    {inProgress ? (
                      <button
                        onClick={runTurn}
                        className="px-9 py-2.5 bg-green-600 hover:bg-green-500 rounded text-white font-bold shadow-md"
                      >
                        ▶ Run Turn
                      </button>
                    ) : (
                      <button
                        onClick={startSession}
                        disabled={selected.mechs.length === 0}
                        className="px-5 py-2.5 bg-green-700 hover:bg-green-600 rounded text-white font-bold shadow-md disabled:opacity-40 disabled:cursor-not-allowed"
                      >
                        ▶ Start Session
                      </button>
                    )}
                    <button
                      onClick={() => setDetailView((v) => (v === 'history' ? 'combat' : 'history'))}
                      className={`px-5 py-2.5 bg-sky-600 hover:bg-sky-500 rounded text-white font-bold shadow-md ${
                        detailView === 'history'
                          ? 'bg-amber-950/40 border-amber-700/50 text-amber-400'
                          : 'bg-gray-900 border-gray-700 hover:bg-gray-800 text-gray-300'
                      }`}
                    >
                      📜 History{selected.events?.length ? ` (${selected.events.length})` : ''}
                    </button>
                  </>
                )}
                {inProgress && (
                  <button
                    onClick={endSession}
                      className="px-5 py-2.5 bg-amber-600 hover:bg-amber-500 rounded text-white font-bold shadow-md"

                    // className="text-xs px-3 py-1.5 bg-orange-950/60 border border-orange-900 hover:bg-orange-900/60 rounded text-orange-300"
                  >
                    ⏹ End Session
                  </button>
                )}
                <button
                  onClick={() => deleteSession(selected.id)}
                  className="px-3 py-2.5 bg-red-600 hover:bg-red-500 rounded text-white font-bold shadow-md"
                >
                  Delete Session
                </button>
              </div>
            </div>

            {/* Body: a completed session is read-only (history only); otherwise
                the History toggle, or lobby (build roster) vs combat. */}
            {completed || detailView === 'history' ? (
              <SessionHistory events={selected.events ?? []} units={selected.mechs} />
            ) : inProgress ? (
              <div className="flex-1 p-6 overflow-y-auto max-w-[1800px] w-full mx-auto space-y-4">
                {enemyUnits.length > 0 && (
                  <div className="flex flex-wrap items-center gap-2 text-xs text-gray-400">
                    <span className="uppercase tracking-wider text-red-400/80 font-bold">
                      Enemy Forces:
                    </span>
                    {enemyUnits.map((e) => (
                      <span
                        key={e.id}
                        className="px-2 py-0.5 rounded bg-red-950/60 border border-red-900 text-red-300"
                      >
                        {e.name} ({e.tonnage ?? '—'}t)
                      </span>
                    ))}
                  </div>
                )}
                {playerUnits.map((unit) => (
                  <SessionMechRow
                    key={`${unit.id}-${selected.current_turn}`}
                    sessionId={selected.id}
                    unit={unit}
                    mech={mechs.find((m) => m.id === unit.mech_id)}
                    enemies={enemyUnits}
                    firedEvent={
                      unit.fire_event_id
                        ? selected.events.find((e) => e.id === unit.fire_event_id)
                        : null
                    }
                    reload={reload}
                  />
                ))}
                {playerUnits.length === 0 && (
                  <div className="text-center text-gray-500 text-sm py-8">
                    No player mechs deployed to fight.
                  </div>
                )}
              </div>
            ) : (
              <div className="flex-1 p-8 overflow-y-auto max-w-3xl w-full mx-auto space-y-6">
                {/* Add a mech */}
                <div className="bg-gray-950 p-4 rounded-lg border border-gray-800 flex flex-wrap gap-3 items-end">
                  <div className="flex-1 min-w-[12rem]">
                    <label className="block text-xs uppercase text-gray-400 mb-1">
                      Deploy Mech from Library
                    </label>
                    <select
                      value={mechToAdd}
                      onChange={(e) => setMechToAdd(e.target.value)}
                      className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-amber-500"
                    >
                      <option value="">Select a chassis…</option>
                      {mechs.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.name} {m.model} - ({m.tonnage}t)
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="flex-1 min-w-[10rem]">
                    <label className="block text-xs uppercase text-gray-400 mb-1">Pilot Name</label>
                    <input
                      type="text"
                      value={pilotName}
                      onChange={(e) => setPilotName(e.target.value)}
                      placeholder="e.g. Natasha Kerensky"
                      className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-amber-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs uppercase text-gray-400 mb-1">Gunnery</label>
                    <select
                      value={pilotGunnery}
                      onChange={(e) => setPilotGunnery(e.target.value)}
                      className="px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-amber-500"
                    >
                      {[0, 1, 2, 3, 4, 5, 6, 7, 8].map((g) => (
                        <option key={g} value={g}>
                          {g}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs uppercase text-gray-400 mb-1">Side</label>
                    <select
                      value={addTeam}
                      onChange={(e) => setAddTeam(e.target.value)}
                      className="px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-amber-500"
                    >
                      <option value="player">Player</option>
                      <option value="enemy">Enemy</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs uppercase text-gray-400 mb-1">Colour</label>
                    <select
                      value={deployColor}
                      onChange={(e) => setDeployColor(e.target.value)}
                      className="px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-amber-500"
                    >
                      {COLOR_PALETTE.map((c) => (
                        <option key={c.id} value={c.id}>
                          {c.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="basis-full flex justify-center">
                    <button
                      onClick={addMech}
                      disabled={!mechToAdd}
                      className="w-full max-w-md px-4 py-2 bg-amber-600 hover:bg-amber-700 rounded text-white text-sm font-bold disabled:opacity-40 disabled:cursor-not-allowed"
                    >
                      Deploy
                    </button>
                  </div>
                </div>

                {/* Deployed roster */}
                <div className="border border-gray-800 rounded-lg bg-gray-950 overflow-hidden">
                  <table className="w-full text-left text-sm">
                    <thead className="bg-gray-900 text-gray-400 text-xs uppercase">
                      <tr>
                        <th className="px-6 py-3">Chassis</th>
                        <th className="px-4 py-3">Pilot</th>
                        <th className="px-4 py-3">Gunnery</th>
                        <th className="px-4 py-3">Side</th>
                        <th className="px-4 py-3">Tonnage</th>
                        <th className="px-4 py-3">Tech</th>
                        <th className="px-4 py-3"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-800 text-gray-300">
                      {selected.mechs.map((unit) => (
                        <tr key={unit.id} className="hover:bg-gray-900/20">
                          <td className="px-6 py-4 text-white font-medium">{unit.name}</td>
                          <td className="px-4 py-4">{unit.pilot_name || '—'}</td>
                          <td className="px-4 py-4 font-mono text-amber-400">
                            {unit.pilot_gunnery_skill ?? '—'}
                          </td>
                          <td className="px-4 py-4">
                            <TeamBadge team={unit.team} />
                          </td>
                          <td className="px-4 py-4">{unit.tonnage ?? '—'}t</td>
                          <td className="px-4 py-4 uppercase text-amber-400 text-xs font-mono">
                            {unit.tech_base ?? '—'}
                          </td>
                          <td className="px-4 py-4 text-right">
                            <button
                              onClick={() => removeUnit(unit.id)}
                              className="text-xs text-red-400 hover:text-red-300"
                            >
                              Remove
                            </button>
                          </td>
                        </tr>
                      ))}
                      {selected.mechs.length === 0 && (
                        <tr>
                          <td colSpan="7" className="px-6 py-8 text-center text-gray-500">
                            No mechs deployed. Add one from the library above.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="flex-1 flex justify-center items-center text-gray-500">
            Select or create a game session to manage its roster.
          </div>
        )}
      </div>
    </div>
  );
}
