import { useState } from 'react';

import { API } from '../../api';
import { TeamBadge } from '../../components/badges';
import { ArmorBar, AsAttackResultView } from './AsAttackResultView';

// One combat card per deployed Alpha Strike unit: its stat line, live
// armor/structure bars, and an attack panel (pick target + range, click Attack).
//
// When ``embedded`` is true the row drops its own outer border + collapse
// header so a parent container (AsUnitWithAi) can own the chrome and keep it
// the same height as a side-by-side AI card.
export function AsMechRow({ sessionId, unit, enemies = [], reload, embedded = false, aiControls = null }) {
  const card = unit.alpha_strike_card;
  const [targetId, setTargetId] = useState('');
  const [distance, setDistance] = useState('6');
  const [pilotSkill, setPilotSkill] = useState('4');
  const [moveMod, setMoveMod] = useState('0');
  const [otherMod, setOtherMod] = useState('0');
  const [result, setResult] = useState(null);
  const [firing, setFiring] = useState(false);
  const [open, setOpen] = useState(true);

  const needsTarget = enemies.length > 0;
  const target = enemies.find((e) => String(e.id) === String(targetId)) ?? null;

  // Armor/structure max come from the card; current from the live session unit.
  const armorMax = card?.armor ?? 0;
  const structMax = card?.structure ?? 0;
  const armorCur = unit.as_armor_current ?? armorMax;
  const structCur = unit.as_structure_current ?? structMax;
  const destroyed = structCur <= 0 && structMax > 0;

  const attack = () => {
    if (!target) return;
    setFiring(true);
    fetch(`${API}/api/sessions/${sessionId}/as-attack`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_mech_id: unit.id,
        target_session_mech_id: target.id,
        distance: parseInt(distance, 10) || 0,
        pilot_skill: parseInt(pilotSkill, 10) || 0,
        attacker_movement_modifier: parseInt(moveMod, 10) || 0,
        additional_modifier: parseInt(otherMod, 10) || 0,
      }),
    })
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.detail || 'Attack failed');
        setResult(body);
        reload?.();
      })
      .catch((err) => alert('Error attacking: ' + err.message))
      .finally(() => setFiring(false));
  };

  // The card body (bars + attack panel + result). Shared by both modes.
  const body = (
    <div className="p-4 flex gap-4 w-full flex-wrap">
      {/* Left: defense bars, with the Automate control pinned to the bottom. */}
      <div className="flex-1 min-w-[16rem] flex flex-col">
        <div className="space-y-4">
          {card ? (
            <>
              <ArmorBar label="Armor" current={armorCur} max={armorMax} color="bg-sky-500" size="lg" />
              <ArmorBar label="Structure" current={structCur} max={structMax} color="bg-amber-500" size="lg" />
            </>
          ) : (
            <div className="text-sm text-red-400">
              No Alpha Strike card for this chassis — add one in the Mechs tab.
            </div>
          )}
        </div>
        {aiControls && <div className="mt-auto pt-4">{aiControls}</div>}
      </div>

      {/* Middle: attack panel */}
      <div className="w-60 shrink-0 border-l border-gray-800 pl-4 space-y-2">
        <div>
          <label className="block text-[10px] uppercase tracking-wider text-red-400/80 mb-1 font-bold">
            Target
          </label>
          {needsTarget ? (
            <select
              value={targetId}
              onChange={(e) => setTargetId(e.target.value)}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-red-500"
            >
              <option value="">Select target</option>
              {enemies.map((e) => (
                <option key={e.id} value={e.id}>
                  {e.name} {e.model ?? ''}
                </option>
              ))}
            </select>
          ) : (
            <div className="text-xs text-gray-500">No enemy units to target.</div>
          )}
        </div>

        <div className="grid grid-cols-2 gap-2">
          <NumField label="Distance (in)" value={distance} onChange={setDistance} />
          <NumField label="Pilot Skill" value={pilotSkill} onChange={setPilotSkill} />
          <NumField label="Move Mod" value={moveMod} onChange={setMoveMod} />
          <NumField label="Other Mod" value={otherMod} onChange={setOtherMod} />
        </div>

        <button
          onClick={attack}
          disabled={!card || firing || (needsTarget && !target) || destroyed}
          className="w-full px-4 py-2 bg-red-700 hover:bg-red-600 rounded text-white text-sm font-bold uppercase tracking-wide disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {firing ? 'Resolving…' : '🎯 Attack'}
        </button>
      </div>

      {/* Right: last attack result */}
      <div className="w-72 shrink-0 border-l border-gray-800 pl-4">
        {result ? (
          <AsAttackResultView result={result} />
        ) : (
          <div className="text-sm text-gray-600 italic">No attack resolved yet.</div>
        )}
      </div>
    </div>
  );

  // Embedded: no outer border/collapse — the parent owns the chrome and height.
  // A compact stat line sits at the top in place of the header.
  if (embedded) {
    return (
      <div className="flex flex-col h-full">
        <div className="flex items-center gap-3 px-4 py-2 border-b border-gray-800 bg-gray-900/30">
          <span className="text-sm text-white font-bold truncate">
            {unit.name} {unit.model ?? ''}
          </span>
          {card && (
            <span className="text-xs text-gray-500 font-mono shrink-0">
              {card.damage_short}/{card.damage_medium}/{card.damage_long} · Sz {card.size ?? '—'} · TMM {card.tmm ?? 0}
            </span>
          )}
          {destroyed && (
            <span className="shrink-0 px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-red-950/70 text-red-400 border border-red-900">
              Destroyed
            </span>
          )}
        </div>
        {body}
      </div>
    );
  }

  // Standalone: self-contained collapsible card (original behavior).
  return (
    <div className="border border-gray-800 rounded-lg bg-gray-950 w-full overflow-hidden">
      {/* Header */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-gray-900/40 border-b border-gray-800"
      >
        <span className={`text-gray-500 text-xs transition-transform ${open ? 'rotate-90' : ''}`}>▶</span>
        <span className="text-lg text-white font-bold truncate">
          {unit.name} {unit.model ?? ''}
        </span>
        <TeamBadge team={unit.team} />
        {card && (
          <span className="text-xs text-gray-500 font-mono shrink-0">
            {card.damage_short}/{card.damage_medium}/{card.damage_long} · Sz {card.size ?? '—'} · TMM {card.tmm ?? 0}
          </span>
        )}
        {destroyed && (
          <span className="shrink-0 px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-red-950/70 text-red-400 border border-red-900">
            Destroyed
          </span>
        )}
      </button>

      {open && body}
    </div>
  );
}

function NumField({ label, value, onChange }) {
  return (
    <div>
      <label className="block text-[10px] uppercase tracking-wider text-gray-400 mb-1">{label}</label>
      <input
        type="number"
        step="1"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-2 py-1.5 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-amber-500"
      />
    </div>
  );
}
