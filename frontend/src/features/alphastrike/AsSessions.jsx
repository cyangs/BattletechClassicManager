import { useState, useEffect } from 'react';

import { API } from '../../api';
import { TeamBadge } from '../../components/badges';
import { AsMechRow } from './AsMechRow';
import { AsAttackResultView } from './AsAttackResultView';
import { AiControlCard } from './AiControlCard';

// Alpha Strike sessions tab: create AS games, deploy units (chassis that have
// an AS card), and resolve attacks. Simpler than Classic — no turn machinery.
export default function AsSessions({ sessions, mechs, reload }) {
  // Only Alpha Strike sessions belong in this tab.
  const asSessions = sessions.filter((s) => s.game_system === 'alpha_strike');

  const [selectedId, setSelectedId] = useState(asSessions[0]?.id ?? null);
  const [newName, setNewName] = useState('');
  const [mode, setMode] = useState('standard');
  const [mechToAdd, setMechToAdd] = useState('');
  const [addTeam, setAddTeam] = useState('player');
  const [view, setView] = useState('combat'); // 'combat' | 'history'
  // The hardcoded Aces AI control-card deck (fetched once); used by the
  // "Automate" button to draw a random card for a unit's role.
  const [aiDeck, setAiDeck] = useState([]);

  useEffect(() => {
    fetch(`${API}/api/ai-cards`)
      .then((r) => r.json())
      .then((d) => setAiDeck(d.cards ?? []))
      .catch(() => setAiDeck([]));
  }, []);

  // Scope selection to AS sessions so a Classic id can never open here.
  const selected = asSessions.find((s) => s.id === selectedId) ?? null;
  // Only chassis with an AS card can be deployed into an AS game.
  const asCapableMechs = mechs.filter((m) => m.alpha_strike_card);

  const createSession = (e) => {
    e.preventDefault();
    if (!newName.trim()) return;
    fetch(`${API}/api/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: newName.trim(),
        game_system: 'alpha_strike',
        as_damage_mode: mode,
        admin_name: 'Admin',
      }),
    })
      .then((r) => r.json())
      .then((created) => {
        setNewName('');
        reload().then(() => setSelectedId(created.id));
      })
      .catch((err) => alert('Error creating session: ' + err));
  };

  const deleteSession = (id) => {
    if (!confirm('Delete this Alpha Strike session?')) return;
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
      body: JSON.stringify({ mech_ids: [parseInt(mechToAdd, 10)], team: addTeam }),
    })
      .then(() => {
        setMechToAdd('');
        reload();
      })
      .catch((err) => alert('Error adding mech: ' + err));
  };

  const removeUnit = (unitId) => {
    fetch(`${API}/api/sessions/${selected.id}/mechs/${unitId}`, { method: 'DELETE' })
      .then(() => reload())
      .catch((err) => alert('Error removing mech: ' + err));
  };

  const playerUnits = selected ? selected.mechs.filter((u) => u.team !== 'enemy') : [];
  const enemyUnits = selected ? selected.mechs.filter((u) => u.team === 'enemy') : [];

  return (
    <div className="flex h-full">
      {/* LEFT: session list + create */}
      <div className="w-80 border-r border-gray-800 bg-gray-950 flex flex-col shrink-0">
        <div className="p-4 border-b border-gray-800">
          <h1 className="text-lg font-bold text-sky-400 mb-3">Alpha Strike Games</h1>
          <form onSubmit={createSession} className="space-y-2">
            <input
              type="text"
              placeholder="New game name..."
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-sm text-white focus:outline-none focus:border-sky-500"
            />
            <div>
              <label className="block text-[10px] uppercase tracking-wider text-gray-400 mb-1">
                Damage Mode
              </label>
              <select
                value={mode}
                onChange={(e) => setMode(e.target.value)}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-sky-500"
              >
                <option value="standard">Standard (all-or-nothing)</option>
                <option value="variable">Variable (2d6 per damage point)</option>
              </select>
            </div>
            <button
              type="submit"
              disabled={!newName.trim()}
              className="w-full px-3 py-2 bg-sky-600 hover:bg-sky-700 rounded text-white text-sm font-bold disabled:opacity-40 disabled:cursor-not-allowed"
            >
              + Create Game
            </button>
          </form>
        </div>

        <div className="flex-1 overflow-y-auto">
          {asSessions.map((s) => (
            <button
              key={s.id}
              onClick={() => {
                setSelectedId(s.id);
                setView('combat');
              }}
              className={`w-full text-left p-4 border-b border-gray-800 transition-colors ${
                selectedId === s.id
                  ? 'bg-sky-950/40 border-l-4 border-l-sky-500'
                  : 'hover:bg-gray-900'
              }`}
            >
              <div className="font-semibold text-white">{s.name}</div>
              <div className="text-xs text-gray-500 mt-0.5">
                {s.mechs.length} unit(s) · {s.as_damage_mode}
              </div>
            </button>
          ))}
          {asSessions.length === 0 && (
            <div className="p-4 text-center text-xs text-gray-500">
              No Alpha Strike games yet. Create one above.
            </div>
          )}
        </div>
      </div>

      {/* RIGHT: detail */}
      <div className="flex-1 flex flex-col bg-gray-900 overflow-hidden">
        {selected ? (
          <>
            <div className="p-6 bg-gray-950 border-b border-gray-800 flex justify-between items-center">
              <div>
                <h2 className="text-3xl font-extrabold text-white">{selected.name}</h2>
                <p className="text-gray-400 text-xs mt-1 font-mono uppercase">
                  Alpha Strike · {selected.as_damage_mode} · {selected.mechs.length} unit(s)
                </p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={() => setView((v) => (v === 'history' ? 'combat' : 'history'))}
                  className="px-5 py-2.5 bg-sky-600 hover:bg-sky-500 rounded text-white font-bold shadow-md"
                >
                  📜 History{selected.events?.length ? ` (${selected.events.length})` : ''}
                </button>
                <button
                  onClick={() => deleteSession(selected.id)}
                  className="px-3 py-2.5 bg-red-600 hover:bg-red-500 rounded text-white font-bold shadow-md"
                >
                  Delete
                </button>
              </div>
            </div>

            {view === 'history' ? (
              <AsHistory events={selected.events ?? []} />
            ) : (
              <div className="flex-1 p-6 overflow-y-auto max-w-[1600px] w-full mx-auto space-y-4">
                {/* Deploy a unit */}
                <div className="bg-gray-950 p-4 rounded-lg border border-gray-800 flex flex-wrap gap-3 items-end">
                  <div className="flex-1 min-w-[14rem]">
                    <label className="block text-xs uppercase text-gray-400 mb-1">
                      Deploy Unit (chassis with an AS card)
                    </label>
                    <select
                      value={mechToAdd}
                      onChange={(e) => setMechToAdd(e.target.value)}
                      className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-sky-500"
                    >
                      <option value="">Select a chassis…</option>
                      {asCapableMechs.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.name} {m.model} — {m.alpha_strike_card.damage_short}/
                          {m.alpha_strike_card.damage_medium}/{m.alpha_strike_card.damage_long}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs uppercase text-gray-400 mb-1">Side</label>
                    <select
                      value={addTeam}
                      onChange={(e) => setAddTeam(e.target.value)}
                      className="px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-sky-500"
                    >
                      <option value="player">Player</option>
                      <option value="enemy">Enemy</option>
                    </select>
                  </div>
                  <button
                    onClick={addMech}
                    disabled={!mechToAdd}
                    className="px-4 py-2 bg-sky-600 hover:bg-sky-700 rounded text-white text-sm font-bold disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    Deploy
                  </button>
                  {asCapableMechs.length === 0 && (
                    <p className="basis-full text-[11px] text-amber-400/80">
                      No chassis have Alpha Strike cards yet. Add cards in the Mechs tab first.
                    </p>
                  )}
                </div>

                {/* Enemy roster summary */}
                {enemyUnits.length > 0 && (
                  <div className="flex flex-wrap items-center gap-2 text-xs text-gray-400">
                    <span className="uppercase tracking-wider text-red-400/80 font-bold">Enemy:</span>
                    {enemyUnits.map((e) => (
                      <span
                        key={e.id}
                        className="px-2 py-0.5 rounded bg-red-950/60 border border-red-900 text-red-300 flex items-center gap-1"
                      >
                        {e.name} {e.model ?? ''} (A{e.as_armor_current ?? '—'}/S{e.as_structure_current ?? '—'})
                        <button
                          onClick={() => removeUnit(e.id)}
                          title="Remove"
                          className="text-red-400 hover:text-red-200"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}

                {/* Player units. Each row can show a drawn AI control card to
                    the LEFT of the unit's combat card (two columns). */}
                <div className="space-y-4">
                  {playerUnits.map((unit) => (
                    <AsUnitWithAi
                      key={unit.id}
                      sessionId={selected.id}
                      unit={unit}
                      enemies={enemyUnits}
                      aiDeck={aiDeck}
                      reload={reload}
                    />
                  ))}
                </div>
                {playerUnits.length === 0 && (
                  <div className="text-center text-gray-500 text-sm py-8">
                    No player units deployed yet.
                  </div>
                )}
              </div>
            )}
          </>
        ) : (
          <div className="flex-1 flex justify-center items-center text-gray-500">
            Select or create an Alpha Strike game.
          </div>
        )}
      </div>
    </div>
  );
}

// A single expandable container holding a player unit's combat card and, once
// an AI control card has been drawn, that card to its LEFT at equal height.
// One header owns the collapse toggle + the Automate / Draw / Clear controls.
function AsUnitWithAi({ sessionId, unit, enemies, aiDeck, reload }) {
  const [drawn, setDrawn] = useState(null);
  const [open, setOpen] = useState(true);

  const role = unit.alpha_strike_card?.role ?? null;
  // Cards whose role matches this unit (case-insensitive). If none match the
  // role, fall back to the whole deck so Automate always produces something.
  const pool = (() => {
    if (!role) return aiDeck;
    const matched = aiDeck.filter(
      (c) => String(c.role ?? '').toUpperCase() === String(role).toUpperCase(),
    );
    return matched.length ? matched : aiDeck;
  })();
  const roleHasCards = pool.length > 0;

  const draw = () => {
    if (!pool.length) return;
    setDrawn(pool[Math.floor(Math.random() * pool.length)]);
    setOpen(true);
  };

  // The large Automate control block, rendered at the bottom of the mech
  // sheet's armor/structure column.
  const aiControls = drawn ? (
    <div className="flex gap-2">
      <button
        onClick={draw}
        className="flex-1 px-4 py-3 bg-sky-700 hover:bg-sky-600 border border-sky-500/50 rounded-lg text-white text-base font-bold shadow-md"
      >
        🎲 Draw Another
      </button>
      <button
        onClick={() => setDrawn(null)}
        className="px-4 py-3 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded-lg text-gray-300 text-base font-bold"
      >
        Clear
      </button>
    </div>
  ) : (
    <button
      onClick={draw}
      disabled={!roleHasCards}
      title={
        roleHasCards
          ? 'Draw a random AI control card for this unit'
          : 'No AI control cards available yet'
      }
      className="w-full px-4 py-4 bg-sky-700 hover:bg-sky-600 border border-sky-500/50 rounded-lg text-white text-lg font-bold uppercase tracking-wide shadow-md disabled:opacity-40 disabled:cursor-not-allowed"
    >
      🤖 Automate{role ? ` (${role})` : ''}
    </button>
  );

  return (
    <div className="border border-gray-800 rounded-lg bg-gray-950 w-full overflow-hidden">
      {/* Single shared header */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-3 px-4 py-3 border-b border-gray-800 text-left hover:bg-gray-900/40"
      >
        <span className={`text-gray-500 text-xs transition-transform ${open ? 'rotate-90' : ''}`}>▶</span>
        <span className="text-lg text-white font-bold truncate">
          {unit.name} {unit.model ?? ''}
        </span>
        <TeamBadge team={unit.team} />
      </button>

      {/* Body: AI card (left) + mech card (right), stretched to equal height. */}
      {open && (
        <div
          className={`grid grid-cols-1 items-stretch divide-y divide-gray-800 ${
            drawn ? 'xl:grid-cols-[minmax(0,24rem)_1fr] xl:divide-y-0 xl:divide-x' : ''
          }`}
        >
          {drawn && <AiControlCard card={drawn} embedded />}
          <AsMechRow
            sessionId={sessionId}
            unit={unit}
            enemies={enemies}
            reload={reload}
            embedded
            aiControls={aiControls}
          />
        </div>
      )}
    </div>
  );
}

// Chronological log of resolved AS attacks (newest first).
function AsHistory({ events }) {
  const attacks = [...events].filter((e) => e.event_type === 'as_attack').reverse();
  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="mx-auto w-full max-w-3xl space-y-3">
        <h3 className="text-xs font-bold uppercase tracking-wider text-sky-400/80">
          Attack Log
        </h3>
        {attacks.length === 0 ? (
          <div className="text-center text-gray-500 text-sm py-8">No attacks yet.</div>
        ) : (
          attacks.map((e) => (
            <div key={e.id} className="border border-gray-800 rounded-lg bg-gray-950 p-4">
              <div className="text-sm text-white font-semibold mb-2">
                <span className="text-sky-400">Turn {e.payload?.turn ?? e.turn}</span> ·{' '}
                {e.attacker} → <span className="text-red-400">{e.target}</span>
              </div>
              <AsAttackResultView result={e.payload} />
            </div>
          ))
        )}
      </div>
    </div>
  );
}
