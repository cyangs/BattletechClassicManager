import { useState, useEffect, useCallback } from 'react';

import { API } from './api';
import MechsLibrary from './components/MechsLibrary';
import WeaponsLibrary from './components/WeaponsLibrary';

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

// Shared by the Sessions tab below.
function TeamBadge({ team }) {
  const enemy = team === 'enemy';
  return (
    <span
      className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
        enemy
          ? 'bg-red-950/60 text-red-400 border border-red-900'
          : 'bg-sky-950/60 text-sky-400 border border-sky-900'
      }`}
    >
      {enemy ? 'Enemy' : 'Player'}
    </span>
  );
}

// Little badges for the chassis-level attachments fitted onto a mech.
function AttachmentBadges({ attachments }) {
  const list = attachments ?? [];
  if (list.length === 0) return null;
  return (
    <div className="mt-3 flex flex-wrap gap-1.5">
      {list.map((a) => (
        <span
          key={a.sku}
          title={a.display_name}
          className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-amber-950/50 text-amber-400 border border-amber-900"
        >
          {a.display_name}
        </span>
      ))}
    </div>
  );
}

// =====================================================================
// TAB 3: SESSIONS — game rooms with deployed mech rosters
// =====================================================================
function Sessions({ sessions, mechs, reload }) {
  const [selectedId, setSelectedId] = useState(sessions[0]?.id ?? null);
  const [newName, setNewName] = useState('');
  const [mechToAdd, setMechToAdd] = useState('');
  const [addTeam, setAddTeam] = useState('player');
  const [pilotName, setPilotName] = useState('');
  const [pilotGunnery, setPilotGunnery] = useState('4');
  const [detailView, setDetailView] = useState('combat'); // 'combat' | 'history'

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
      }),
    })
      .then(() => {
        setMechToAdd('');
        setPilotName('');
        setPilotGunnery('4');
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
                  {m.name} ({m.tonnage}t)
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
                          {m.name} ({m.tonnage}t)
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
                  <button
                    onClick={addMech}
                    disabled={!mechToAdd}
                    className="px-4 py-2 bg-amber-600 hover:bg-amber-700 rounded text-white text-sm font-bold disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Deploy
                  </button>
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

// One combat row per deployed mech: weapon selection + fire + results.
function SessionMechRow({ sessionId, unit, mech, enemies = [], firedEvent = null, reload }) {
  const links = mech?.weapon_links ?? [];
  // Expand each mounted link into one row per weapon instance (a link mounted
  // in count N becomes N individually-selectable rows), so the player fires
  // each weapon separately rather than the whole group at once.
  const instances = links.flatMap((link) =>
    Array.from({ length: Math.max(1, link.count) }, (_, i) => ({
      key: `${link.id}#${i}`,
      linkId: link.id,
      name: link.weapon?.full_name || link.weapon?.name,
      location: link.location,
      heat: link.heat,
    })),
  );
  // Weapon instances disabled for the session (carried forward across turns).
  const disabledWeapons = new Set(unit.disabled_weapons ?? []);
  // A logged fire this turn means this unit has already fired (Fire is spent
  // until the turn advances or the fire is undone).
  const firedThisTurn = !!unit.fired_this_turn;

  const [selected, setSelected] = useState(() => new Set());
  const [targetUnitId, setTargetUnitId] = useState('');
  const [facing, setFacing] = useState('Front/Rear');
  const [selfMovementModifier, setSelfMovementModifier] = useState('0');
  const [targetMovementModifier, setTargetMovementModifier] = useState('0');
  const [distanceModifier, setDistanceModifier] = useState('0')
  const [additionalModifier, setAdditionalModifier] = useState('0');
  // Seed from the persisted event so a reload (or turn keep-alive) still shows
  // this turn's resolved shots; local state covers the immediate fire response.
  const [result, setResult] = useState(firedEvent?.payload ?? null);
  const [firing, setFiring] = useState(false);

  const toggle = (id) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const target = enemies.find((e) => String(e.id) === String(targetUnitId)) ?? null;
  const needsTarget = enemies.length > 0;

  // Every weapon instance the unit can still fire this turn (disabled ones excluded).
  const fireableInstances = instances.filter((inst) => !disabledWeapons.has(inst.key));

  // Resolve a fire for the given weapon link ids (one entry per shot).
  const doFire = (weaponLinkIds) => {
    if (weaponLinkIds.length === 0) return;
    setFiring(true);
    fetch(`${API}/api/sessions/${sessionId}/fire`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        mech_id: unit.mech_id,
        session_mech_id: unit.id,
        // One link id per instance fired; a link fires once per entry.
        weapon_link_ids: weaponLinkIds,
        pilot_gunnery_skill: unit.pilot_gunnery_skill ?? 4,
        target_mech_id: target ? target.mech_id : null,
        facing,
        distance_modifier: parseInt(distanceModifier, 10) || 0,
        additional_modifier: parseInt(additionalModifier, 10) || 0,
        self_movement_modifier: parseInt(selfMovementModifier, 10) || 0,
        target_movement_modifier: parseInt(targetMovementModifier, 10) || 0,
      }),
    })
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.detail || 'Fire failed');
        setResult(body);
        reload?.(); // refetch so fired_this_turn greys out the Fire button
      })
      .catch((err) => alert('Error firing weapons: ' + err.message))
      .finally(() => setFiring(false));
  };

  // Fire only the checked (and enabled) weapons.
  const fire = () =>
    doFire(
      fireableInstances
        .filter((inst) => selected.has(inst.key))
        .map((inst) => inst.linkId),
    );

  // Alpha strike: select and fire every enabled weapon at once.
  const alphaStrike = () => {
    setSelected(new Set(fireableInstances.map((inst) => inst.key)));
    doFire(fireableInstances.map((inst) => inst.linkId));
  };

  // Undo this turn's fire: drop the logged event so the unit can fire again.
  const undoFire = () => {
    const eventId = unit.fire_event_id ?? firedEvent?.id;
    if (!eventId) return;
    fetch(`${API}/api/sessions/${sessionId}/events/${eventId}`, { method: 'DELETE' })
      .then(async (res) => {
        if (!res.ok) throw new Error('Undo failed');
        setResult(null);
        reload?.();
      })
      .catch((err) => alert('Error undoing fire: ' + err.message));
  };

  // Toggle a weapon instance's disabled state; persists for the whole session.
  const toggleDisabled = (weaponKey) => {
    const nextDisabled = !disabledWeapons.has(weaponKey);
    if (nextDisabled) {
      // Can't keep a disabled weapon selected for firing.
      setSelected((prev) => {
        const next = new Set(prev);
        next.delete(weaponKey);
        return next;
      });
    }
    fetch(`${API}/api/sessions/${sessionId}/mechs/${unit.id}/weapon-state`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ weapon_key: weaponKey, disabled: nextDisabled }),
    })
      .then(async (res) => {
        if (!res.ok) throw new Error('Update failed');
        reload?.();
      })
      .catch((err) => alert('Error updating weapon: ' + err.message));
  };

  return (
    <div className="border border-gray-800 rounded-lg bg-gray-950 p-4 flex gap-4 w-full">
      {/* Left: mech + selectable weapons */}
      <div className="flex-1 min-w-0 max-w-md">
        <div className="mb-3">
          <div className="flex justify-between items-center gap-2">
            <div className="flex items-center gap-2 min-w-0">
              <span className="text-2xl text-white font-bold truncate">{unit.name} {unit.model ?? mech?.model ?? ''}</span>
              <TeamBadge team={unit.team} />
            </div>
            <span className="text-sm text-gray-500 font-mono uppercase shrink-0">
              {unit.tonnage ?? '—'}t · {unit.tech_base ?? '—'}
            </span>
          </div>
          <div className="text-sm text-gray-400 font-mono uppercase mt-2">
            {unit.pilot_name ? `${unit.pilot_name} · ` : ''}Gunnery {unit.pilot_gunnery_skill ?? 4}
          </div>
        </div>

        {instances.length === 0 ? (
          <div className="text-sm text-gray-500">No weapons mounted on this chassis.</div>
        ) : (
          <div className="space-y-1.5">
            {instances.map((inst) => {
              const isDisabled = disabledWeapons.has(inst.key);
              return (
                <div key={inst.key} className="flex items-center gap-2 py-1">
                  <label
                    className={`flex flex-1 min-w-0 items-center gap-2 text-sm ${
                      isDisabled
                        ? 'text-gray-600 line-through cursor-not-allowed'
                        : 'text-gray-300 cursor-pointer'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selected.has(inst.key) && !isDisabled}
                      onChange={() => toggle(inst.key)}
                      disabled={isDisabled || firedThisTurn}
                      className="w-4 h-4 accent-amber-600 disabled:opacity-40"
                    />
                    <span className="text-sm truncate font-mono">{inst.name}</span>
                    <span className="text-xs text-gray-500 font-mono">· {inst.location}</span>
                    <span className="text-xs text-gray-500 font-mono">· {inst.heat}</span>
                  </label>
                  <button
                    type="button"
                    onClick={() => toggleDisabled(inst.key)}
                    title={isDisabled ? 'Re-enable weapon' : 'Disable weapon for the session'}
                    className={`ml-auto shrink-0 w-5 h-5 flex items-center justify-center rounded text-xs font-bold leading-none ${
                      isDisabled
                        ? 'bg-red-900/70 text-red-200 border border-red-700'
                        : 'text-gray-500 hover:text-red-400 hover:bg-red-950/40'
                    }`}
                  >
                    ✕
                  </button>
                </div>
              );
            })}
          </div>
        )}

        <div className="mt-4 flex gap-2">
          <button
            onClick={fire}
            disabled={selected.size === 0 || firing || firedThisTurn || (needsTarget && !target)}
            className="px-4 py-2 bg-red-700 hover:bg-red-600 rounded text-white text-sm font-bold uppercase tracking-wide disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {firedThisTurn ? '✓ Fired This Turn' : '🔥 Fire Weapons'}
          </button>
          <button
            onClick={alphaStrike}
            disabled={fireableInstances.length === 0 || firing || firedThisTurn || (needsTarget && !target)}
            title="Fire every weapon at once"
            className="px-4 py-2 bg-amber-700 hover:bg-amber-600 rounded text-white text-sm font-bold uppercase tracking-wide disabled:opacity-40 disabled:cursor-not-allowed"
          >
            ☢ Alpha Strike
          </button>
        </div>

      <AttachmentBadges attachments={mech?.attachments ?? unit.attachments} />

        {firedThisTurn && (
          <div className="mt-2">
            <button
              onClick={undoFire}
              className="text-xs px-2 py-1 bg-gray-900 border border-gray-700 hover:bg-gray-800 rounded text-amber-400"
            >
              ↩ Undo Fire
            </button>
          </div>
        )}
      </div>

      {/* Middle: target selection */}
      <div className="w-56 shrink-0 border-l border-gray-800 pl-4 space-y-3">
        <div>
          <label className="text-base uppercase tracking-wider text-red-400/80 mb-1 font-bold">
            Target
          </label>
          {needsTarget ? (
            <select
              value={targetUnitId}
              onChange={(e) => setTargetUnitId(e.target.value)}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-red-500"
            >
              <option value="">Select Target</option>
              {enemies.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.name} ({e.tonnage ?? '—'}t) - {e.pilot_name}
                </option>
              ))}
            </select>
          ) : (
            <div className="text-xs text-gray-500">No enemy forces to target.</div>
          )}
        </div>

        <div>
          <label className="block text-[10px] uppercase tracking-wider text-gray-400 mb-1">
            Facing
          </label>
          <select
            value={facing}
            onChange={(e) => setFacing(e.target.value)}
            className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-amber-500"
          >
            <option value="Left Side">Left Side</option>
            <option value="Front/Rear">Front/Rear</option>
            <option value="Right Side">Right Side</option>
          </select>
        </div>

        <div>
          <label className="block text-[10px] uppercase tracking-wider text-gray-400 mb-1">
            Self Movement Modifier
          </label>
          <input
            type="number"
            step="1"
            value={selfMovementModifier}
            onChange={(e) => setSelfMovementModifier(e.target.value)}
            className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-amber-500"
          />
        </div>

        <div>
          <label className="block text-[10px] uppercase tracking-wider text-gray-400 mb-1">
            Target Movement Modifier
          </label>
          <input
            type="number"
            step="1"
            value={targetMovementModifier}
            onChange={(e) => setTargetMovementModifier(e.target.value)}
            className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-amber-500"
          />
        </div>

        <div>
          <label className="block text-[10px] uppercase tracking-wider text-gray-400 mb-1">
            Distance to Target
          </label>
          <input
            type="number"
            step="1"
            value={distanceModifier}
            onChange={(e) => setDistanceModifier(e.target.value)}
            className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-amber-500"
          />
        </div>

        <div>
          <label className="block text-[10px] uppercase tracking-wider text-gray-400 mb-1">
            Additional Modifiers
          </label>
          <input
            type="number"
            step="1"
            value={additionalModifier}
            onChange={(e) => setAdditionalModifier(e.target.value)}
            className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-amber-500"
          />
        </div>
      </div>

      {/* Right: fire results */}
      {/* Arbitrarily Defined column width here since this is an important data column */}
      <div className="w-96 shrink-0 border-l border-gray-800 pl-4">
        {result ? (
          <FireResults result={result} />
        ) : (
          <div className="text-base text-gray-600 italic">No fire resolved yet.</div>
        )}
      </div>

      {/* Far right: damage totalled by target hit location */}
      <div className="w-56 border-l border-gray-800 pl-4 flex flex-col items-end">
        {result ? (
          <DamageByLocation result={result} />
        ) : (
          <div className="text-base text-gray-600 italic">No damage yet.</div>
        )}
      </div>
    </div>
  );
}

// Summarizes a fire result as total damage dealt to each of the target's
// locations (hits only), most-damaged first.
function DamageByLocation({ result }) {
  const byLocation = {};
  (result.shots ?? []).forEach((s) => {
    if (!s.hit) return;
    if (s.cluster_hits) {
      // Cluster weapon: each cluster landed its own damage on its own location.
      s.cluster_hits.forEach((h) => {
        byLocation[h.location] = (byLocation[h.location] || 0) + (h.damage || 0);
      });
    } else if (s.hit_location) {
      byLocation[s.hit_location] = (byLocation[s.hit_location] || 0) + (s.damage || 0);
    }
  });
  const rows = Object.entries(byLocation).sort((a, b) => b[1] - a[1]);
  const total = rows.reduce((sum, [, dmg]) => sum + dmg, 0);

  return (
    <div className="text-base space-y-2 text-right">
      <div className="text-large font-bold uppercase tracking-wider text-amber-500/80">
        Damage by Location
      </div>
      {rows.length === 0 ? (
        <div className="text-gray-600 italic">No damage dealt.</div>
      ) : (
        <>
          <div className="space-y-1">
            {rows.map(([location, dmg]) => (
              <div
                key={location}
                className="flex items-center justify-end gap-2 rounded border border-gray-800 bg-gray-900/40 px-2 py-1"
              >
                <span className="truncate text-gray-200">{location}</span>
                <span className="shrink-0 font-bold text-amber-400">{dmg}</span>
              </div>
            ))}
          </div>
          <div className="flex items-center justify-end gap-2 border-t border-gray-800 pt-1.5 font-bold text-amber-400">
            <span>Total</span>
            <span>{total}</span>
          </div>
        </>
      )}
    </div>
  );
}

// History view: the chronological log of session events (newest first).
// Theoretical 2d6 outcome weights (out of 36) — the ideal bell curve overlaid
// on the actual rolls so a turn's luck is easy to eyeball.
const TWO_D6_WEIGHTS = { 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1 };

// Pull every 2d6 total rolled across a set of fire events: to-hit rolls, hit
// location rolls, through-armor-crit rerolls, and cluster-table rolls.
function collectTurnRolls(events) {
  const rolls = [];
  (events ?? []).forEach((e) => {
    (e.payload?.shots ?? []).forEach((s) => {
      const r = s.all_rolls;
      if (r) {
        if (r.to_hit_1 != null && r.to_hit_2 != null) rolls.push(r.to_hit_1 + r.to_hit_2);
        if (r.location_1 != null && r.location_2 != null) rolls.push(r.location_1 + r.location_2);
        if (r.tac_reroll_1 != null && r.tac_reroll_2 != null) rolls.push(r.tac_reroll_1 + r.tac_reroll_2);
      }
      if (s.cluster_roll != null) rolls.push(s.cluster_roll);
    });
  });
  return rolls;
}

// Histogram of a turn's 2d6 rolls (bars) against the ideal distribution (curve),
// with the mean and standard deviation of what was actually rolled.
function RollDistribution({ turn, events }) {
  const rolls = collectTurnRolls(events);
  const n = rolls.length;
  const values = [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];

  const counts = Object.fromEntries(values.map((v) => [v, 0]));
  rolls.forEach((r) => {
    if (r >= 2 && r <= 12) counts[r] += 1;
  });

  const mean = n ? rolls.reduce((a, b) => a + b, 0) / n : 0;
  const sd = n ? Math.sqrt(rolls.reduce((a, b) => a + (b - mean) ** 2, 0) / n) : 0;
  const expected = values.map((v) => (n * TWO_D6_WEIGHTS[v]) / 36);
  const yMax = Math.max(1, ...values.map((v) => counts[v]), ...expected);

  // SVG geometry.
  const W = 240, H = 108, padL = 6, padR = 6, padT = 8, padB = 16;
  const chartW = W - padL - padR;
  const chartH = H - padT - padB;
  const step = chartW / values.length;
  const barW = step * 0.7;
  const barX = (i) => padL + i * step + (step - barW) / 2;
  const midX = (i) => padL + i * step + step / 2;
  const yOf = (val) => padT + chartH - (val / yMax) * chartH;

  return (
    <div className="rounded-lg border border-gray-800 bg-gray-950 p-3">
      <div className="flex items-baseline justify-between mb-1">
        <span className="text-xs font-bold text-amber-400">Turn {turn}</span>
        <span className="text-[10px] font-mono text-gray-500">n={n}</span>
      </div>
      {n === 0 ? (
        <div className="py-4 text-center text-[10px] italic text-gray-600">No dice rolled.</div>
      ) : (
        <>
          <svg viewBox={`0 0 ${W} ${H}`} className="w-full">
            {/* Actual rolls: bar per 2d6 total (7 highlighted as the peak). */}
            {values.map((v, i) => (
              <rect
                key={v}
                x={barX(i)}
                y={yOf(counts[v])}
                width={barW}
                height={padT + chartH - yOf(counts[v])}
                rx="1"
                className={v === 7 ? 'fill-amber-500' : 'fill-amber-700/70'}
              />
            ))}
            {/* Ideal 2d6 distribution scaled to this sample size. */}
            <polyline
              fill="none"
              stroke="currentColor"
              strokeWidth="1"
              className="text-sky-400/80"
              points={values.map((v, i) => `${midX(i)},${yOf(expected[i])}`).join(' ')}
            />
            {values.map((v, i) => (
              <circle key={`e${v}`} cx={midX(i)} cy={yOf(expected[i])} r="1.3" className="fill-sky-400/80" />
            ))}
            {/* x-axis labels (2..12). */}
            {values.map((v, i) => (
              <text key={`l${v}`} x={midX(i)} y={H - 4} textAnchor="middle" fontSize="7" className="fill-gray-500">
                {v}
              </text>
            ))}
          </svg>
          <div className="mt-1 text-right text-[10px] font-mono text-gray-500">
            μ={mean.toFixed(1)} · σ={sd.toFixed(1)}
          </div>
          <div className="mt-0.5 text-right text-[10px] text-gray-600 italic">
            Mean and Standard Deviation of the all rolls this turn
          </div>
          <div className="mt-0.5 text-right text-[10px] text-gray-600 italic">
            Most commonly rolled vs. how close to center the spread is
          </div>
        </>
      )}
    </div>
  );
}

function SessionHistory({ events, units }) {
  const unitName = (id) => units.find((u) => u.id === id)?.name;
  // Group events by turn, newest turn first; the chart for a turn sits to the
  // right of that same turn's event cards.
  const turns = [...new Set(events.map((e) => e.turn))].sort((a, b) => b - a);

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="mx-auto w-full max-w-7xl space-y-6">
        <h3 className="text-xs font-bold uppercase tracking-wider text-amber-500/80">
          Session History
        </h3>
        {turns.length === 0 ? (
          <div className="text-center text-gray-500 text-sm py-8">
            No events yet. Fire weapons and run turns to build the log.
          </div>
        ) : (
          turns.map((t) => {
            const turnEvents = events.filter((e) => e.turn === t).reverse(); // newest first within turn
            return (
              <div key={t} className="flex items-start gap-6">
                {/* Left: this turn's event log */}
                <div className="min-w-0 flex-1 space-y-3">
                  {turnEvents.map((e) => (
                    <div key={e.id} className="border border-gray-800 rounded-lg bg-gray-950 p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="text-sm text-white font-semibold">
                          <span className="text-amber-400">Turn {e.turn}</span> ·{' '}
                          {e.attacker || unitName(e.session_mech_id) || 'Unknown'}
                          {e.target && (
                            <>
                              {' → '}
                              <span className="text-red-400">{e.target}</span>
                            </>
                          )}
                        </div>
                        <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-gray-800 border border-gray-700 text-gray-400">
                          {e.event_type}
                        </span>
                      </div>
                      <FireResults result={e.payload} />
                    </div>
                  ))}
                </div>

                {/* Right: this turn's 2d6 roll distribution */}
                <div className="w-96 shrink-0">
                  <RollDistribution turn={t} events={events.filter((e) => e.turn === t)} />
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}

function FireResults({ result }) {
  return (
    <div className="text-xs space-y-2">
      {result.target && (
        <div className="text-base text-gray-300 font-bold">
          Target: <span className="text-base text-red-400 font-bold">{result.target}</span>
        </div>
      )}
      {result.facing && (
        <div className="text-gray-500 font-mono">
          {result.facing} · TMM {result.target_movement_modifier >= 0 ? '+' : ''}
          {result.target_movement_modifier}
        </div>
      )}
      <div className="text-gray-400">
        Turn {result.turn} ·{' '}
        <span className="text-green-400">{result.hits} hit</span> /{' '}
        <span className="text-red-400">{result.misses} miss</span>
      </div>
      <div className="space-y-1.5">
        {result.shots.map((s, i) => (
          <div
            key={i}
            className={`rounded border px-2.5 py-2 ${
              s.hit ? 'bg-green-950/25 border-green-900/60' : 'bg-gray-900/40 border-gray-800'
            }`}
          >
            {/* Weapon + outcome */}
            <div className="flex items-center justify-between gap-2">
              <div className="min-w-0">
                <div className="truncate text-gray-200 font-medium text-lg">{s.weapon}</div>
              </div>
              <span
                className={`shrink-0 w-48 font-bold uppercase px-1.5 py-0.5 rounded ${
                  s.hit
                    ? 'bg-green-900/60 text-green-300 border border-green-800'
                    : 'bg-red-950/60 text-red-400 border border-red-900'
                }`}
              >
                {s.hit ? `Hit · ${s.damage} Damage` : 'Miss'}
              </span>
            </div>

            {/* Hit location(s) — a single badge, or a cluster spread */}
            {s.hit && s.cluster_hits ? (
              <div className="mt-1.5 space-y-1">
                <div className="text-[10px] font-mono text-gray-500 text-right pr-9">
                  Cluster: rolled {s.cluster_roll} → {s.cluster_hits_landed} pts
                </div>
                <div className="flex flex-col items-end gap-1">
                  {s.cluster_hits.map((h, j) => (
                      <span
                          key={j}
                          className={`shrink-0 w-48 bold uppercase px-1.5 py-0.5 rounded border ${
                              h.location.toLowerCase() === "head" || h.critical_hit
                                  ? "bg-red-900/40 text-red-300 border-red-800"
                                  : "bg-yellow-900/40 text-yellow-300 border-yellow-800"
                          }`}
                      >
                    {h.damage} → {h.location}
                    {h.critical_hit && " ✶ CRIT"}
                  </span>
                  ))}
                </div>
              </div>
            ) : s.hit ? (
              <div className="mt-1.5 flex justify-end">
                <span
                    className={`shrink-0 w-48 bold uppercase px-1.5 py-0.5 rounded border ${
                        s.hit_location.toLowerCase() === "head" || s.critical_hit
                            ? "bg-red-900/40 text-red-300 border-red-800"
                            : "bg-yellow-900/40 text-yellow-300 border-yellow-800"
                    }`}
                >
                  {s.hit_location}
                  {s.critical_hit && " ✶ CRIT"}
                </span>
              </div>
            ) : null}

            {/* Individual 2d6 rolls that make up the shot */}
            {s.all_rolls ? (
              <div className="mt-1.5 space-y-1 font-mono text-[11px]">
                {/* To-hit roll: dice, total, and the number needed */}
                <div className="flex items-center gap-1.5">
                  <span className="w-16 shrink-0 uppercase text-gray-500">To Hit</span>
                  <Die value={s.all_rolls.to_hit_1} />
                  <Die value={s.all_rolls.to_hit_2} />
                  <span className="text-gray-600">=</span>
                  <span className="font-bold text-gray-100">{s.roll}</span>
                  <span className="text-gray-600">vs</span>
                  <span className="font-bold text-amber-400">
                    {s.target_number <= 2 ? "AUTO HIT" : `Need ${s.target_number}+`}
                  </span>
                </div>
                {/* Location roll: only rolled on a hit */}
                {s.hit && s.all_rolls.location_1 != null && (
                  <div className="flex items-center gap-1.5">
                    <span className="w-16 shrink-0 uppercase text-gray-500">Location</span>
                    <Die value={s.all_rolls.location_1} />
                    <Die value={s.all_rolls.location_2} />
                    <span className="text-gray-600">=</span>
                    <span className="font-bold text-gray-100">{s.all_rolls.location_1 + s.all_rolls.location_2}</span>
                  </div>
                )}
                {/* Through-armor critical reroll: only rolled when the location roll is a natural 2 */}
                {s.all_rolls.tac_reroll_1 != null && s.all_rolls.tac_reroll_2 != null && (
                  <div className="flex items-center gap-1.5">
                    <span className="w-16 shrink-0 uppercase text-red-500">Critical</span>
                    <Die value={s.all_rolls.tac_reroll_1} />
                    <Die value={s.all_rolls.tac_reroll_2} />
                    <span className="text-gray-600">=</span>
                    <span className="font-bold text-red-300">{s.all_rolls.tac_reroll_1 + s.all_rolls.tac_reroll_2}</span>
                  </div>
                )}
              </div>
            ) : (
              <div className="mt-1.5 font-mono text-[11px] text-gray-500">Out of range</div>
            )}
          </div>
        ))}
      </div>
      <div className="pt-1.5 border-t border-gray-800 text-amber-400 font-bold">
        {result.total_damage} Total Damage · {result.total_heat} Total Heat
      </div>
    </div>
  );
}

// A single d6 face rendered as a small pip box.
function Die({ value }) {
  return (
    <span className="inline-flex items-center justify-center w-5 h-5 rounded bg-gray-800 border border-gray-600 text-gray-100 text-[10px] font-bold">
      {value}
    </span>
  );
}
