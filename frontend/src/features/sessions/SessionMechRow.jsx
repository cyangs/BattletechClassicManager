import { useState } from 'react';

import { API } from '../../api';
import { COLOR_PALETTE } from '../../lib/palette';
import { TeamBadge } from '../../components/badges';
import { AttachmentBadges } from './AttachmentBadges';
import { FireResults } from './FireResults';
import { DamageByLocation } from './DamageByLocation';

// One combat row per deployed mech: weapon selection + fire + results.
export function SessionMechRow({ sessionId, unit, mech, enemies = [], firedEvent = null, reload }) {
  // The unit owns a session-private copy of its loadout (snapshotted when it
  // was deployed). Each weapon row is one fireable instance and carries its own
  // destroyed (knocked out) flag, so damage is tracked per session without ever
  // touching the master chassis.
  const weaponRows = unit.weapons ?? [];
  const instances = weaponRows.map((w) => ({
    key: w.id,
    id: w.id,
    name: w.full_name || w.name,
    location: w.location,
    heat: w.heat,
    destroyed: w.destroyed,
    // ULTRA ballistics can double-tap (fire twice) in a single turn.
    isUltra: (w.weapon_type || '').toUpperCase() === 'ULTRA',
  }));
  const attachments = unit.attachments ?? [];
  // A logged fire this turn means this unit has already fired (Fire is spent
  // until the turn advances or the fire is undone).
  const firedThisTurn = !!unit.fired_this_turn;

  const [selected, setSelected] = useState(() => new Set());
  // Weapon instances flagged to double-tap this fire (ULTRA ballistics only).
  const [doubleTap, setDoubleTap] = useState(() => new Set());
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
  const [open, setOpen] = useState(true);

  // Accent colour lets players distinguish duplicate chassis at a glance.
  // Seeded from the value stored on the unit (set at deploy time); can be
  // changed locally during the session without touching the server.
  const [accentColorId, setAccentColorId] = useState(unit.accent_color ?? 'none');
  const accent = COLOR_PALETTE.find((c) => c.id === accentColorId) ?? COLOR_PALETTE[0];

  const toggle = (id) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const toggleDoubleTap = (id) =>
    setDoubleTap((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const target = enemies.find((e) => String(e.id) === String(targetUnitId)) ?? null;
  const needsTarget = enemies.length > 0;

  // Every weapon instance the unit can still fire this turn (destroyed ones excluded).
  const fireableInstances = instances.filter((inst) => !inst.destroyed);

  // Resolve a fire for the given session weapon ids (one entry per shot).
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
        // Of those, which fired double-tap (ULTRA ballistics).
        double_tap_ids: weaponLinkIds.filter((id) => doubleTap.has(id)),
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
        .map((inst) => inst.id),
    );

  // Alpha strike: select and fire every enabled weapon at once.
  const alphaStrike = () => {
    setSelected(new Set(fireableInstances.map((inst) => inst.key)));
    doFire(fireableInstances.map((inst) => inst.id));
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

  // Drop a weapon instance from the current fire selection (used when it can no
  // longer fire — e.g. it was just destroyed).
  const deselect = (weaponId) =>
    setSelected((prev) => {
      const next = new Set(prev);
      next.delete(weaponId);
      return next;
    });

  // Post a boolean state change (destroyed) for one weapon instance.
  const postWeaponFlag = (path, body) =>
    fetch(`${API}/api/sessions/${sessionId}/mechs/${unit.id}/${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
      .then(async (res) => {
        if (!res.ok) throw new Error('Update failed');
        reload?.();
      })
      .catch((err) => alert('Error updating weapon: ' + err.message));

  // Toggle a weapon instance's destroyed state (combat damage).
  const toggleDestroyed = (inst) => {
    const nextDestroyed = !inst.destroyed;
    if (nextDestroyed) deselect(inst.id); // a destroyed weapon can't fire
    postWeaponFlag('weapon-destroyed', { session_weapon_id: inst.id, destroyed: nextDestroyed });
  };

  // Toggle an attachment's destroyed state (combat damage).
  const toggleAttachmentDestroyed = (attachment) =>
    fetch(`${API}/api/sessions/${sessionId}/mechs/${unit.id}/attachment-destroyed`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_attachment_id: attachment.id,
        destroyed: !attachment.destroyed,
      }),
    })
      .then(async (res) => {
        if (!res.ok) throw new Error('Update failed');
        reload?.();
      })
      .catch((err) => alert('Error updating attachment: ' + err.message));

  return (
    <div className="border border-gray-800 rounded-lg bg-gray-950 w-full overflow-hidden">
      {/* Collapsible header — always visible */}
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors border-b ${
          accent.id === 'none'
            ? 'border-gray-800 hover:bg-gray-900/40'
            : `${accent.bg} ${accent.border}`
        }`}
      >
        <span className={`text-gray-500 text-xs transition-transform duration-150 ${open ? 'rotate-90' : ''}`}>
          ▶
        </span>
        <div className="flex-1 min-w-0">
          <div className="flex items-baseline gap-2 min-w-0">
            <span className="text-lg text-white font-bold truncate">
              {unit.name} {unit.model ?? mech?.model ?? ''}
            </span>
            <span className="text-xs text-gray-500 font-mono uppercase shrink-0">
              {unit.tonnage ?? '—'}t · {unit.tech_base ?? '—'}
            </span>
          </div>
          <div className="text-xs text-gray-400 font-mono uppercase mt-0.5 truncate">
            {unit.pilot_name ? `${unit.pilot_name} · ` : ''}Gunnery {unit.pilot_gunnery_skill ?? 4}
          </div>
        </div>
        <TeamBadge team={unit.team} />
        {firedThisTurn && (
          <span className="shrink-0 px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-green-950/60 text-green-400 border border-green-900">
            ✓ Fired
          </span>
        )}
        {result && !firedThisTurn && (
          <span className="shrink-0 text-[10px] text-gray-500 font-mono">
            {result.hits}/{result.shots?.length ?? 0} hits · {result.total_damage} dmg
          </span>
        )}
      </button>

      {/* Expandable body */}
      {open && (
      <div className="p-4 flex gap-4 w-full">
      {/* Left: mech + selectable weapons */}
      <div className="flex-1 min-w-0 max-w-md">
        {instances.length === 0 ? (
          <div className="text-sm text-gray-500">No weapons mounted on this chassis.</div>
        ) : (
          <div className="space-y-1.5">
            {instances.map((inst) => {
              const isDestroyed = inst.destroyed;
              return (
                <div key={inst.key} className="py-1">
                  <div className="flex items-center gap-2">
                    <label
                      className={`flex flex-1 min-w-0 items-center gap-2 text-sm ${
                        isDestroyed
                          ? 'text-gray-600 line-through cursor-not-allowed'
                          : 'text-gray-300 cursor-pointer'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={selected.has(inst.key) && !isDestroyed}
                        onChange={() => toggle(inst.key)}
                        disabled={isDestroyed || firedThisTurn}
                        className="w-4 h-4 accent-amber-600 disabled:opacity-40"
                      />
                      <span className={`text-sm truncate font-mono ${isDestroyed ? 'text-red-500/70' : ''}`}>
                        {inst.name}
                      </span>
                      <span className="text-xs text-gray-500 font-mono">· {inst.location}</span>
                      {inst.heat != null && (
                        <span className="text-xs text-gray-500 font-mono">· {inst.heat} Heat</span>
                      )}
                      {isDestroyed && (
                        <span className="text-[10px] uppercase font-bold text-red-400 border border-red-800 rounded px-1 no-underline">
                          Destroyed
                        </span>
                      )}
                    </label>
                    {/* Destroy / repair (combat damage) */}
                    <button
                      type="button"
                      onClick={() => toggleDestroyed(inst)}
                      title={isDestroyed ? 'Repair weapon' : 'Mark weapon destroyed'}
                      className={`shrink-0 w-5 h-5 flex items-center justify-center rounded text-xs font-bold leading-none ${
                        isDestroyed
                          ? 'bg-red-800 text-red-100 border border-red-600'
                          : 'text-gray-500 hover:text-red-400 hover:bg-red-950/40'
                      }`}
                    >
                      ✕
                    </button>
                  </div>
                  {/* ULTRA ballistics can fire twice in one turn. */}
                  {inst.isUltra && !isDestroyed && (
                    <label className="ml-6 mt-0.5 flex items-center gap-1.5 text-[10px] uppercase font-bold tracking-wider text-orange-400 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={doubleTap.has(inst.key)}
                        onChange={() => toggleDoubleTap(inst.key)}
                        disabled={firedThisTurn}
                        className="w-3.5 h-3.5 accent-orange-500 disabled:opacity-40"
                      />
                      Double Tap!
                    </label>
                  )}
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

      <AttachmentBadges attachments={attachments} onToggle={toggleAttachmentDestroyed} />

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
      )}
    </div>
  );
}
