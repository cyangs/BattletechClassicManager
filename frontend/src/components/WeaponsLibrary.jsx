import { useState, useEffect, useCallback } from 'react';

import { API } from '../api';
import {AmmoBadge, LabeledInput, TechBaseBadge} from './shared';

// Format a to-hit modifier for display: "+2", "-3", 0, or "—" when unset.
function fmtMod(v) {
  if (v == null) return '—';
  return v > 0 ? `+${v}` : String(v);
}

const CATALOG_TABS = [
  { id: 'weapons', label: '⚔️ Weapons' },
  { id: 'attachments', label: '🔧 Attachments' },
  { id: 'ammo', label: '🧨 Ammo' },
];

// Weapon system categories (mirrors backend WeaponType enum).
const WEAPON_TYPES = ['MISSILE', 'BALLISTIC', 'LASER', 'PPC', 'ARTY', 'OTHER'];

// Ballistic-only sub-classification, stored on modifications.weapon_type.
const BALLISTIC_SUBTYPES = ['NONE', 'ULTRA'];

// =====================================================================
// TAB 2: WEAPONS LIBRARY — weapons / attachments / ammo catalogs
// =====================================================================
// Shell for the Weapons Master Catalog: three sub-catalogs (weapons,
// attachments, ammo). Weapons come in from the top-level load; attachments and
// ammo are fetched here and refreshed after edits.
export default function WeaponsLibrary({ weapons, reload }) {
  const [catalog, setCatalog] = useState('weapons');
  const [attachments, setAttachments] = useState([]);
  const [ammo, setAmmo] = useState([]);

  const loadAttachments = useCallback(
    () => fetch(`${API}/api/weapon-attachments`).then((r) => r.json()).then(setAttachments),
    [],
  );
  const loadAmmo = useCallback(
    () => fetch(`${API}/api/ammo-types`).then((r) => r.json()).then(setAmmo),
    [],
  );
  useEffect(() => {
    loadAttachments();
    loadAmmo();
  }, [loadAttachments, loadAmmo]);

  return (
    <div className="h-full overflow-y-auto p-8">
      <div className="max-w-screen-2xl mx-auto">
        <div className="flex items-center gap-4 mb-6">
          <h1 className="text-2xl font-bold text-amber-500 whitespace-nowrap">
            Weapons & Parts Master Catalog
          </h1>
          <nav className="flex gap-1">
            {CATALOG_TABS.map((t) => (
              <button
                key={t.id}
                onClick={() => setCatalog(t.id)}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  catalog === t.id
                    ? 'bg-amber-950/40 text-amber-400 border border-amber-700/50'
                    : 'text-gray-400 hover:text-white hover:bg-gray-900'
                }`}
              >
                {t.label}
              </button>
            ))}
          </nav>
        </div>

        {catalog === 'weapons' && <WeaponsCatalog weapons={weapons} reload={reload} />}
        {catalog === 'attachments' && (
          <AttachmentsCatalog attachments={attachments} reload={loadAttachments} />
        )}
        {catalog === 'ammo' && <AmmoCatalog ammo={ammo} reload={loadAmmo} />}
      </div>
    </div>
  );
}

function WeaponsCatalog({ weapons, reload }) {
  const [query, setQuery] = useState('');
  // null = closed, {} = new weapon, weapon object = editing that weapon
  const [editing, setEditing] = useState(null);
  const filtered = weapons.filter((w) =>
    `${w.full_name || ''} ${w.name}`.toLowerCase().includes(query.toLowerCase()),
  );

  return (
    <>
      <div className="flex justify-end items-center gap-3 mb-4">
        <input
          type="text"
          placeholder="Filter weapons..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-64 px-3 py-2 bg-gray-950 border border-gray-700 rounded text-sm text-white focus:outline-none focus:border-amber-500"
        />
        <button
          onClick={() => setEditing({})}
          className="px-4 py-2 bg-amber-600 hover:bg-amber-700 rounded text-white text-sm font-bold whitespace-nowrap"
        >
          + New Weapon
        </button>
      </div>

      <div className="border border-gray-800 rounded-lg bg-gray-950 overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-900 text-gray-400 text-xs uppercase">
            <tr>
              <th className="px-6 py-3">Tech Base</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-6 py-3">Weapon System</th>
              <th className="px-4 py-3">Damage</th>
              <th className="px-4 py-3">Heat</th>
              <th className="px-4 py-3">Ammo</th>
              <th className="px-4 py-3">Range Brackets (min / S / M / L)</th>
              <th className="px-4 py-3">Hit Modifiers at Range (S / M / L)</th>
              <th className="px-4 py-3">Cluster (shots × dmg)</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800 text-gray-300">
            {filtered.map((w) => (
              <tr key={w.id} className="hover:bg-gray-900/20">
                <td className="px-4 py-4 w-20">
                  <TechBaseBadge techBase={w.tech_base} />
                </td>
                <td className="px-4 py-4 w-20">
                  <WeaponTypeBadge weaponType={w.type} />
                </td>
                <td className="px-6 py-4 text-white font-medium">{w.full_name || w.name}</td>
                <td className="px-4 py-4 font-bold text-amber-500">{w.damage}</td>
                <td className="px-4 py-4 text-red-400">{w.heat}</td>
                <td className="px-4 py-4">
                  <AmmoBadge use={w.use_ammo} />
                </td>
                <td className="px-4 py-4 font-mono text-xs text-gray-400">
                  {w.minimum_range ?? '—'} / {w.short_range ?? '—'} / {w.medium_range ?? '—'} /{' '}
                  {w.long_range ?? '—'}
                </td>
                <td className="px-4 py-4 font-mono text-xs text-gray-400">
                  {fmtMod(w.short_range_modifier)} / {fmtMod(w.medium_range_modifier)} /{' '}
                  {fmtMod(w.long_range_modifier)}
                </td>
                <td className="px-4 py-4 font-mono text-xs text-gray-400">
                  {w.num_shots ? `${w.num_shots} × ${w.cluster_damage ?? '—'}` : '—'}
                </td>
                <td className="px-4 py-4 text-right">
                  <button
                    onClick={() => setEditing(w)}
                    className="text-xs text-amber-400 hover:text-amber-300"
                  >
                    Edit
                  </button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan="8" className="px-6 py-8 text-center text-gray-500">
                  No weapons in the catalog match your filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {editing && (
        <WeaponEditor
          weapon={editing.id ? editing : null}
          onClose={() => setEditing(null)}
          onSaved={() => {
            reload();
            setEditing(null);
          }}
        />
      )}
    </>
  );
}

function WeaponEditor({ weapon, onClose, onSaved }) {
  const [weaponType, setWeaponType] = useState((weapon?.type || '').toUpperCase());
  const [ballisticSubtype, setBallisticSubtype] = useState(
    weapon?.modifications?.weapon_type || 'NONE',
  );

  const handleSubmit = (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const num = (v) => (v === '' || v == null ? null : parseInt(v, 10));

    // Preserve any existing modifications, then apply the ballistic sub-type.
    const modifications = { ...(weapon?.modifications || {}) };
    if (weaponType === 'BALLISTIC' && ballisticSubtype === 'ULTRA') {
      modifications.weapon_type = 'ULTRA';
    } else {
      delete modifications.weapon_type;
    }

    const payload = {
      id: weapon ? weapon.id : null,
      name: fd.get('name'),
      full_name: fd.get('full_name') || null,
      use_ammo: fd.get('use_ammo') === 'on',
      damage: num(fd.get('damage')),
      heat: num(fd.get('heat')),
      minimum_range: num(fd.get('minimum_range')),
      short_range: num(fd.get('short_range')),
      medium_range: num(fd.get('medium_range')),
      long_range: num(fd.get('long_range')),
      short_range_modifier: num(fd.get('short_range_modifier')),
      medium_range_modifier: num(fd.get('medium_range_modifier')),
      long_range_modifier: num(fd.get('long_range_modifier')),
      num_shots: num(fd.get('num_shots')),
      cluster_damage: num(fd.get('cluster_damage')),
      type: weaponType || null,
      modifications: Object.keys(modifications).length ? modifications : null,
    };

    fetch(`${API}/api/weapons/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.detail || 'Save failed');
        onSaved();
      })
      .catch((err) => alert('Error saving weapon: ' + err.message));
  };

  return (
    <div
      className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-gray-950 border border-gray-800 rounded-lg shadow-xl w-full max-w-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center px-6 py-4 border-b border-gray-800">
          <h3 className="text-lg font-bold text-white">
            {weapon ? `Edit ${weapon.full_name || weapon.name}` : 'New Weapon System'}
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-xl leading-none">
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4 text-sm">
          <LabeledInput
            name="full_name"
            label="Display Name"
            defaultValue={weapon?.full_name || ''}
            placeholder="e.g. Clan ER Large Laser"
          />
          <LabeledInput
            name="name"
            label="SKU (internal name)"
            defaultValue={weapon?.name || ''}
            required
            maxLength={50}
            className="font-mono text-xs"
          />

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs uppercase text-gray-400 mb-1">Type</label>
              <select
                name="type"
                value={weaponType}
                onChange={(e) => setWeaponType(e.target.value)}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white focus:outline-none focus:border-amber-500"
              >
                <option value="">— None —</option>
                {WEAPON_TYPES.map((t) => (
                  <option key={t} value={t}>
                    {t.charAt(0) + t.slice(1).toLowerCase()}
                  </option>
                ))}
              </select>
            </div>

            {weaponType === 'BALLISTIC' && (
              <div>
                <label className="block text-xs uppercase text-gray-400 mb-1">Ballistic Class</label>
                <select
                  name="ballistic_subtype"
                  value={ballisticSubtype}
                  onChange={(e) => setBallisticSubtype(e.target.value)}
                  className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white focus:outline-none focus:border-amber-500"
                >
                  {BALLISTIC_SUBTYPES.map((s) => (
                    <option key={s} value={s}>
                      {s.charAt(0) + s.slice(1).toLowerCase()}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <LabeledInput name="damage" label="Damage" type="number" min="0" defaultValue={weapon?.damage ?? 0} required />
            <LabeledInput name="heat" label="Heat" type="number" min="0" defaultValue={weapon?.heat ?? 0} required />
          </div>

          <div className="grid grid-cols-4 gap-3">
            <LabeledInput name="minimum_range" label="Min Rng" type="number" min="0" defaultValue={weapon?.minimum_range ?? ''} />
            <LabeledInput name="short_range" label="Short" type="number" min="0" defaultValue={weapon?.short_range ?? ''} />
            <LabeledInput name="medium_range" label="Medium" type="number" min="0" defaultValue={weapon?.medium_range ?? ''} />
            <LabeledInput name="long_range" label="Long" type="number" min="0" defaultValue={weapon?.long_range ?? ''} />
          </div>

          {/* Per-range-band to-hit modifiers (may be negative, e.g. pulse lasers). */}
          <div>
            <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">
              To-Hit Modifier by Range Band
            </div>
            <div className="grid grid-cols-3 gap-3">
              <LabeledInput name="short_range_modifier" label="Short Mod" type="number" defaultValue={weapon?.short_range_modifier ?? ''} />
              <LabeledInput name="medium_range_modifier" label="Medium Mod" type="number" defaultValue={weapon?.medium_range_modifier ?? ''} />
              <LabeledInput name="long_range_modifier" label="Long Mod" type="number" defaultValue={weapon?.long_range_modifier ?? ''} />
            </div>
          </div>

          {/* Cluster weapons (LRM/SRM): shot count and damage per cluster hit. */}
          <div>
            <div className="text-[10px] uppercase tracking-wider text-gray-500 mb-1">
              Cluster (LRM / SRM)
            </div>
            <div className="grid grid-cols-2 gap-3">
              <LabeledInput name="num_shots" label="# Shots" type="number" min="1" defaultValue={weapon?.num_shots ?? ''} />
              <LabeledInput name="cluster_damage" label="Cluster Dmg" type="number" min="0" defaultValue={weapon?.cluster_damage ?? ''} />
            </div>
          </div>

          <label className="flex items-center gap-2 text-gray-300">
            <input
              type="checkbox"
              name="use_ammo"
              defaultChecked={weapon?.use_ammo || false}
              className="w-4 h-4 accent-amber-600"
            />
            Requires ammunition
          </label>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-900 border border-gray-700 hover:bg-gray-800 rounded text-gray-300 text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-amber-600 hover:bg-amber-700 font-bold rounded text-white text-sm"
            >
              {weapon ? '💾 Save Changes' : '⚙️ Create Weapon'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// --- Weapon attachments catalog (Artemis IV, etc.) ---
function AttachmentsCatalog({ attachments, reload }) {
  const [query, setQuery] = useState('');
  const [editing, setEditing] = useState(null); // null closed, {} new, row = edit
  const filtered = attachments.filter((a) =>
    `${a.display_name} ${a.sku}`.toLowerCase().includes(query.toLowerCase()),
  );

  return (
    <>
      <div className="flex justify-end items-center gap-3 mb-4">
        <input
          type="text"
          placeholder="Filter attachments..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-64 px-3 py-2 bg-gray-950 border border-gray-700 rounded text-sm text-white focus:outline-none focus:border-amber-500"
        />
        <button
          onClick={() => setEditing({})}
          className="px-4 py-2 bg-amber-600 hover:bg-amber-700 rounded text-white text-sm font-bold whitespace-nowrap"
        >
          + New Attachment
        </button>
      </div>

      <div className="border border-gray-800 rounded-lg bg-gray-950 overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-900 text-gray-400 text-xs uppercase">
            <tr>
              <th className="px-4 py-3">Tech Base</th>
              <th className="px-4 py-3">Type</th>
              <th className="px-6 py-3">Attachment</th>
              <th className="px-4 py-3">SKU</th>
              <th className="px-4 py-3">To-Hit Mod</th>
              <th className="px-4 py-3">Cluster Mod</th>
              <th className="px-4 py-3">Tonnage</th>
              <th className="px-4 py-3">Description</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800 text-gray-300">
            {filtered.map((a) => (
              <tr key={a.sku} className="hover:bg-gray-900/20">
                <td className="px-4 py-4 w-20">
                  <TechBaseBadge techBase={a.tech_base} />
                </td>
                <td className="px-4 py-4 w-20">
                  <AttachmentTypeBadge attachment_type={a.attachment_type} />
                </td>
                <td className="px-6 py-4 text-white font-medium">{a.display_name}</td>
                <td className="px-4 py-4 font-mono text-xs text-gray-400">{a.sku}</td>
                <td className="px-4 py-4 font-mono text-amber-400">{fmtMod(a.to_hit_modifier)}</td>
                <td className="px-4 py-4 font-mono text-amber-400">{fmtMod(a.cluster_modifier)}</td>
                <td className="px-4 py-4 font-mono text-xs text-gray-400">{a.tonnage ?? '—'}</td>
                <td className="px-4 py-4 text-xs text-gray-400 max-w-md truncate">
                  {a.description || '—'}
                </td>
                <td className="px-4 py-4 text-right">
                  <button
                    onClick={() => setEditing(a)}
                    className="text-xs text-amber-400 hover:text-amber-300"
                  >
                    Edit
                  </button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                  No attachments match your filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {editing && (
        <AttachmentEditor
          attachment={editing.sku ? editing : null}
          onClose={() => setEditing(null)}
          onSaved={() => {
            reload();
            setEditing(null);
          }}
        />
      )}
    </>
  );
}

function AttachmentTypeBadge({ attachment_type }) {
  const isWeaponAttachment = attachment_type === 'weapon';

  return (
    <span
      className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
        isWeaponAttachment
          ? 'bg-red-950/60 text-red-400 border border-red-900'
          : 'bg-gray-800/60 text-gray-300 border border-gray-700'
      }`}
    >
      {isWeaponAttachment ? 'Weapon' : 'Mech'}
    </span>
  );
}

function WeaponTypeBadge({ weaponType }) {
  const weaponTypeBadgeMap = {
    MISSILE:   { label: 'Missile',    classes: 'bg-red-950/60 text-red-400 border border-red-900' },
    BALLISTIC: { label: 'Ballistic',  classes: 'bg-blue-950/60 text-blue-400 border border-blue-900' },
    LASER:     { label: 'Laser',      classes: 'bg-amber-950/60 text-amber-400 border border-amber-900' },
    PPC:       { label: 'PPC',        classes: 'bg-amber-950/60 text-amber-400 border border-amber-900' },
    ARTY:      { label: 'Artillery',  classes: 'bg-amber-950/60 text-amber-400 border border-amber-900' },
    OTHER:     { label: 'Other',      classes: 'bg-amber-950/60 text-amber-400 border border-amber-900' },
  };

  const key = (weaponType || '').toUpperCase();
  const weaponTypeBadge = weaponTypeBadgeMap[key] || {
    label: 'Unknown',
    classes: 'bg-gray-800/60 text-gray-300 border border-gray-700'
  };

  return (
    <span className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${weaponTypeBadge.classes}`}>
      {weaponTypeBadge.label}
    </span>
  );
}


function AttachmentEditor({ attachment, onClose, onSaved }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const num = (v) => (v === '' || v == null ? null : parseInt(v, 10));
    const flt = (v) => (v === '' || v == null ? null : parseFloat(v));
    const payload = {
      sku: fd.get('sku'),
      display_name: fd.get('display_name'),
      to_hit_modifier: num(fd.get('to_hit_modifier')),
      cluster_modifier: num(fd.get('cluster_modifier')),
      tonnage: flt(fd.get('tonnage')),
      description: fd.get('description') || null,
    };

    fetch(`${API}/api/weapon-attachments/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.detail || 'Save failed');
        onSaved();
      })
      .catch((err) => alert('Error saving attachment: ' + err.message));
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-gray-950 border border-gray-800 rounded-lg shadow-xl w-full max-w-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center px-6 py-4 border-b border-gray-800">
          <h3 className="text-lg font-bold text-white">
            {attachment ? `Edit ${attachment.display_name}` : 'New Attachment'}
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-xl leading-none">
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4 text-sm">
          <LabeledInput
            name="display_name"
            label="Display Name"
            defaultValue={attachment?.display_name || ''}
            placeholder="e.g. Artemis IV FCS"
            required
          />
          <LabeledInput
            name="sku"
            label="SKU (id)"
            defaultValue={attachment?.sku || ''}
            required
            maxLength={50}
            readOnly={!!attachment}
            className={`font-mono text-xs ${attachment ? 'opacity-60 cursor-not-allowed' : ''}`}
          />
          <div className="grid grid-cols-2 gap-4">
            <LabeledInput name="to_hit_modifier" label="To-Hit Modifier" type="number" defaultValue={attachment?.to_hit_modifier ?? ''} />
            <LabeledInput name="cluster_modifier" label="Cluster Modifier" type="number" defaultValue={attachment?.cluster_modifier ?? ''} />
            <LabeledInput name="tonnage" label="Tonnage" type="number" step="0.5" min="0" defaultValue={attachment?.tonnage ?? ''} />

          </div>
          <div>
            <label className="block text-xs uppercase text-gray-400 mb-1">Description</label>
            <textarea
              name="description"
              defaultValue={attachment?.description || ''}
              rows={3}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white focus:outline-none focus:border-amber-500"
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-900 border border-gray-700 hover:bg-gray-800 rounded text-gray-300 text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-amber-600 hover:bg-amber-700 font-bold rounded text-white text-sm"
            >
              {attachment ? '💾 Save Changes' : '⚙️ Create Attachment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// --- Ammo types catalog (Inferno, etc.) ---
function AmmoCatalog({ ammo, reload }) {
  const [query, setQuery] = useState('');
  const [editing, setEditing] = useState(null);
  const filtered = ammo.filter((a) =>
    `${a.display_name} ${a.sku}`.toLowerCase().includes(query.toLowerCase()),
  );

  return (
    <>
      <div className="flex justify-end items-center gap-3 mb-4">
        <input
          type="text"
          placeholder="Filter ammo..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="w-64 px-3 py-2 bg-gray-950 border border-gray-700 rounded text-sm text-white focus:outline-none focus:border-amber-500"
        />
        <button
          onClick={() => setEditing({})}
          className="px-4 py-2 bg-amber-600 hover:bg-amber-700 rounded text-white text-sm font-bold whitespace-nowrap"
        >
          + New Ammo
        </button>
      </div>

      <div className="border border-gray-800 rounded-lg bg-gray-950 overflow-hidden">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-900 text-gray-400 text-xs uppercase">
            <tr>
              <th className="px-6 py-3">Ammo Type</th>
              <th className="px-4 py-3">SKU</th>
              <th className="px-4 py-3">Damage</th>
              <th className="px-4 py-3">Heat</th>
              <th className="px-4 py-3">Special</th>
              <th className="px-4 py-3">Description</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-800 text-gray-300">
            {filtered.map((a) => (
              <tr key={a.sku} className="hover:bg-gray-900/20">
                <td className="px-6 py-4 text-white font-medium">{a.display_name}</td>
                <td className="px-4 py-4 font-mono text-xs text-gray-400">{a.sku}</td>
                <td className="px-4 py-4 font-bold text-amber-500">{a.damage ?? '—'}</td>
                <td className="px-4 py-4 text-red-400">{a.heat ?? '—'}</td>
                <td className="px-4 py-4 text-xs text-gray-300">{a.special_effect || '—'}</td>
                <td className="px-4 py-4 text-xs text-gray-400 max-w-md truncate">
                  {a.description || '—'}
                </td>
                <td className="px-4 py-4 text-right">
                  <button
                    onClick={() => setEditing(a)}
                    className="text-xs text-amber-400 hover:text-amber-300"
                  >
                    Edit
                  </button>
                </td>
              </tr>
            ))}
            {filtered.length === 0 && (
              <tr>
                <td colSpan="7" className="px-6 py-8 text-center text-gray-500">
                  No ammo types match your filter.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {editing && (
        <AmmoEditor
          ammo={editing.sku ? editing : null}
          onClose={() => setEditing(null)}
          onSaved={() => {
            reload();
            setEditing(null);
          }}
        />
      )}
    </>
  );
}

function AmmoEditor({ ammo, onClose, onSaved }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const num = (v) => (v === '' || v == null ? null : parseInt(v, 10));
    const payload = {
      sku: fd.get('sku'),
      display_name: fd.get('display_name'),
      damage: num(fd.get('damage')),
      heat: num(fd.get('heat')),
      special_effect: fd.get('special_effect') || null,
      description: fd.get('description') || null,
    };

    fetch(`${API}/api/ammo-types/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.detail || 'Save failed');
        onSaved();
      })
      .catch((err) => alert('Error saving ammo: ' + err.message));
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div
        className="bg-gray-950 border border-gray-800 rounded-lg shadow-xl w-full max-w-lg"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center px-6 py-4 border-b border-gray-800">
          <h3 className="text-lg font-bold text-white">
            {ammo ? `Edit ${ammo.display_name}` : 'New Ammo Type'}
          </h3>
          <button onClick={onClose} className="text-gray-400 hover:text-white text-xl leading-none">
            ×
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4 text-sm">
          <LabeledInput
            name="display_name"
            label="Display Name"
            defaultValue={ammo?.display_name || ''}
            placeholder="e.g. Inferno SRM"
            required
          />
          <LabeledInput
            name="sku"
            label="SKU (id)"
            defaultValue={ammo?.sku || ''}
            required
            maxLength={50}
            readOnly={!!ammo}
            className={`font-mono text-xs ${ammo ? 'opacity-60 cursor-not-allowed' : ''}`}
          />
          <div className="grid grid-cols-2 gap-4">
            <LabeledInput name="damage" label="Damage" type="number" min="0" defaultValue={ammo?.damage ?? ''} />
            <LabeledInput name="heat" label="Heat" type="number" min="0" defaultValue={ammo?.heat ?? ''} />
          </div>
          <LabeledInput
            name="special_effect"
            label="Special Effect"
            defaultValue={ammo?.special_effect || ''}
            maxLength={50}
            placeholder="e.g. Fire, Cluster, AP"
          />
          <div>
            <label className="block text-xs uppercase text-gray-400 mb-1">Description</label>
            <textarea
              name="description"
              defaultValue={ammo?.description || ''}
              rows={3}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white focus:outline-none focus:border-amber-500"
            />
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-gray-900 border border-gray-700 hover:bg-gray-800 rounded text-gray-300 text-sm"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-amber-600 hover:bg-amber-700 font-bold rounded text-white text-sm"
            >
              {ammo ? '💾 Save Changes' : '⚙️ Create Ammo'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
