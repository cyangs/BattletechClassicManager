import { useEffect, useState } from 'react';

import { API } from '../api';
import { AmmoBadge, LabeledInput } from './shared';

// =====================================================================
// TAB 1: MECHS LIBRARY — roster sidebar + overview / weapons / editor
// =====================================================================
export default function MechsLibrary({ mechs, weapons, reload }) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedId, setSelectedId] = useState(mechs[0]?.id ?? null);

  // Derive the selected chassis from the live roster so it always reflects
  // fresh data after a reload (e.g. following an edit). `null` = create mode.
  const selectedMech = selectedId == null ? null : mechs.find((m) => m.id === selectedId) ?? null;

  const filteredMechs = mechs.filter((mech) =>
    mech.name.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <div className="flex h-full">
      {/* LEFT: ROSTER & SEARCH */}
      <div className="w-80 border-r border-gray-800 bg-gray-950 flex flex-col shrink-0">
        <div className="p-4 border-b border-gray-800">
          <div className="flex justify-between items-center mb-3">
            <h1 className="text-lg font-bold text-amber-500">Mech Registry</h1>
            <button
              onClick={() => setSelectedId(null)}
              className="text-xs px-2 py-1 bg-gray-900 border border-gray-700 hover:bg-gray-800 rounded text-amber-500"
            >
              + New
            </button>
          </div>
          <input
            type="text"
            placeholder="Filter mechs by name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-sm text-white focus:outline-none focus:border-amber-500"
          />
        </div>

        <div className="flex-1 overflow-y-auto">
          {filteredMechs.map((mech) => (
            <button
              key={mech.id}
              onClick={() => setSelectedId(mech.id)}
              className={`w-full text-left p-4 border-b border-gray-800 transition-colors flex justify-between items-center ${
                selectedMech?.id === mech.id
                  ? 'bg-amber-950/40 border-l-4 border-l-amber-500'
                  : 'hover:bg-gray-900'
              }`}
            >
              <div>
                <div className="font-semibold text-white">{mech.name} {mech.model}</div>
                <div className="text-xs text-amber-500/70 font-mono mt-0.5 uppercase">
                  {mech.tech_base}
                </div>
              </div>
              <span className="text-xs px-2 py-0.5 rounded bg-gray-800 border border-gray-700">
                {mech.tonnage}t
              </span>
            </button>
          ))}
          {filteredMechs.length === 0 && (
            <div className="p-4 text-center text-xs text-gray-500">No mechs match your filter.</div>
          )}
        </div>
      </div>

      {/* RIGHT: DETAIL PANEL */}
      <div className="flex-1 flex flex-col bg-gray-900 overflow-hidden">
        <div className="p-6 bg-gray-950 border-b border-gray-800">
          <h2 className="text-3xl font-extrabold text-white">
            {selectedMech ? selectedMech.name : 'New Chassis'}
          </h2>
          <p className="text-gray-400 text-xs mt-1 font-mono">
            UUID: {selectedMech?.uuid || 'N/A'}
          </p>
        </div>

        {/* Three columns side by side */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 items-start">
            <Section title="📊 Readout Overview">
              {selectedMech ? (
                <div className="space-y-4">
                  <MechOverview mech={selectedMech} />
                  <MechAttachments mech={selectedMech} reload={reload} />
                </div>
              ) : (
                <ColumnHint>Select a chassis to view its readout.</ColumnHint>
              )}
            </Section>

            <Section title="⚔️ Weapons Array">
              {selectedMech ? (
                <MechWeapons mech={selectedMech} weapons={weapons} reload={reload} />
              ) : (
                <ColumnHint>Save a chassis first, then mount weapons here.</ColumnHint>
              )}
            </Section>

            <Section title="🛠️ Blueprint Editor">
              <MechEditor
                mech={selectedMech}
                onSaved={() => reload()}
                onNewMode={() => setSelectedId(null)}
              />
            </Section>
          </div>
        </div>
      </div>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section>
      <h3 className="text-xs font-bold uppercase tracking-wider text-amber-500/80 mb-3">{title}</h3>
      {children}
    </section>
  );
}

function ColumnHint({ children }) {
  return (
    <div className="bg-gray-950 border border-dashed border-gray-800 rounded-lg p-6 text-center text-sm text-gray-500">
      {children}
    </div>
  );
}

function MechOverview({ mech }) {
  return (
    <div className="bg-gray-950 p-6 rounded-lg border border-gray-800 shadow-md">
      <h3 className="text-lg font-bold text-white mb-4 border-b border-gray-800 pb-2">
        Technical Readout
      </h3>
      <div className="grid grid-cols-2 gap-4 text-sm">
        <Field label="Designation" value={mech.name} />
        <Field label="Model Config" value={mech.model || 'Prime'} />
        <Field label="Technology Base" value={mech.tech_base} accent uppercase />
        <Field label="Chassis Weight" value={`${mech.tonnage} Tons`} />
      </div>
    </div>
  );
}

function Field({ label, value, accent, uppercase }) {
  return (
    <div className="bg-gray-900 p-3 rounded">
      <span className="text-gray-400 text-xs block">{label}</span>
      <strong className={`${accent ? 'text-amber-400' : ''} ${uppercase ? 'uppercase' : ''}`}>
        {value}
      </strong>
    </div>
  );
}

// Chassis-level equipment (attachment_type "mech") pulled from the catalog and
// made available to fit onto the selected mech. Fitted attachments persist via
// the mech_attachment_link table; the mech's current set arrives on the mech
// object as `mech.attachments`.
function MechAttachments({ mech, reload }) {
  const [catalog, setCatalog] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    fetch(`${API}/api/weapon-attachments?attachment_type=mech`)
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.detail || 'Failed to load attachments');
        return body;
      })
      .then((rows) => {
        if (!cancelled) setCatalog(rows);
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const fittedSkus = new Set((mech.attachments ?? []).map((a) => a.sku));

  const toggle = (sku) => {
    const fitted = fittedSkus.has(sku);
    const req = fitted
      ? fetch(`${API}/api/mechs/${mech.id}/attachments/${sku}`, { method: 'DELETE' })
      : fetch(`${API}/api/mechs/${mech.id}/attachments`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ sku }),
        });
    req
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.detail || 'Update failed');
        reload();
      })
      .catch((err) => alert('Error updating attachment: ' + err.message));
  };

  return (
    <div className="bg-gray-950 p-6 rounded-lg border border-gray-800 shadow-md">
      <h3 className="text-lg font-bold text-white mb-4 border-b border-gray-800 pb-2">
        Chassis Equipment
      </h3>

      {error && <div className="text-sm text-red-400 mb-3">{error}</div>}

      <div className="border border-gray-800 rounded-lg bg-gray-900 divide-y divide-gray-800">
        {catalog.map((a) => {
          const fitted = fittedSkus.has(a.sku);
          return (
            <div key={a.sku} className="flex items-center justify-between px-4 py-3">
              <div className="min-w-0">
                <div className="text-white text-sm font-medium truncate">{a.display_name}</div>
                <div className="text-xs text-gray-400 font-mono mt-0.5">
                  {a.tonnage != null ? `${a.tonnage}t` : '—'}
                  {a.tech_base ? ` · ${a.tech_base}` : ''}
                </div>
              </div>
              <button
                onClick={() => toggle(a.sku)}
                className={`text-xs px-3 py-1 rounded border shrink-0 ml-2 ${
                  fitted
                    ? 'bg-amber-950/40 border-amber-600 text-amber-400 hover:bg-amber-950/60'
                    : 'bg-gray-900 border-gray-700 text-amber-500 hover:bg-gray-800'
                }`}
              >
                {fitted ? '✓ Fitted' : '+ Add'}
              </button>
            </div>
          );
        })}
        {catalog.length === 0 && !error && (
          <div className="px-4 py-8 text-center text-gray-500 text-sm">
            No mech attachments in the catalog.
          </div>
        )}
      </div>
    </div>
  );
}

const MECH_LOCATIONS = [
  'HD',
  'CT',
  'LT',
  'RT',
  'LA',
  'RA',
  'LL',
  'RL',
];

function MechWeapons({ mech, weapons, reload }) {
  const [weaponId, setWeaponId] = useState('');
  const [count, setCount] = useState(1);
  const [location, setLocation] = useState('Center Torso');

  const addWeapon = () => {
    if (!weaponId) return;
    fetch(`${API}/api/mechs/${mech.id}/weapons`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        weapon_id: parseInt(weaponId, 10),
        count: parseInt(count, 10) || 1,
        location,
      }),
    })
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.detail || 'Add failed');
        setWeaponId('');
        setCount(1);
        reload();
      })
      .catch((err) => alert('Error adding weapon: ' + err.message));
  };

  const removeLink = (linkId) => {
    fetch(`${API}/api/mechs/${mech.id}/weapons/${linkId}`, { method: 'DELETE' })
      .then(() => reload())
      .catch((err) => alert('Error removing weapon: ' + err));
  };

  const links = mech.weapon_links ?? [];

  return (
    <div className="space-y-4">
      {/* Add-weapon form */}
      <div className="bg-gray-950 p-4 rounded-lg border border-gray-800 space-y-3">
        <div>
          <label className="block text-xs uppercase text-gray-400 mb-1">Mount Weapon</label>
          <select
            value={weaponId}
            onChange={(e) => setWeaponId(e.target.value)}
            className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-amber-500"
          >
            <option value="">Select from catalog…</option>
            {weapons.map((w) => (
              <option key={w.id} value={w.id}>
                {w.full_name || w.name}
              </option>
            ))}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="block text-xs uppercase text-gray-400 mb-1">Qty</label>
            <input
              type="number"
              min="1"
              value={count}
              onChange={(e) => setCount(e.target.value)}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-amber-500"
            />
          </div>
          <div>
            <label className="block text-xs uppercase text-gray-400 mb-1">Location</label>
            <select
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white text-sm focus:outline-none focus:border-amber-500"
            >
              {MECH_LOCATIONS.map((loc) => (
                <option key={loc} value={loc}>
                  {loc}
                </option>
              ))}
            </select>
          </div>
        </div>
        <button
          onClick={addWeapon}
          disabled={!weaponId}
          className="w-full py-2 bg-amber-600 hover:bg-amber-700 font-bold rounded text-white text-sm disabled:opacity-40 disabled:cursor-not-allowed"
        >
          + Mount to Hardpoint
        </button>
      </div>

      {/* Mounted weapons list */}
      <div className="border border-gray-800 rounded-lg bg-gray-950 divide-y divide-gray-800">
        {links.map((link) => (
          <div key={link.id} className="flex items-center justify-between px-4 py-3">
            <div className="min-w-0">
              <div className="text-white text-sm font-medium truncate">
                <span className="text-amber-500 font-bold">{link.count}x</span>{' '}
                {link.weapon?.full_name || link.weapon?.name}
              </div>
              <div className="text-xs text-gray-400 font-mono mt-0.5">{link.location}</div>
            </div>
            <div className="flex items-center gap-3 shrink-0 ml-2">
              <AmmoBadge use={link.weapon?.use_ammo} />
              <button
                onClick={() => removeLink(link.id)}
                title="Remove hardpoint"
                className="text-gray-500 hover:text-red-400 text-lg leading-none"
              >
                ×
              </button>
            </div>
          </div>
        ))}
        {links.length === 0 && (
          <div className="px-4 py-8 text-center text-gray-500 text-sm">
            No weapons mapped to this chassis layout.
          </div>
        )}
      </div>
    </div>
  );
}

function MechEditor({ mech, onSaved, onNewMode }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const payload = {
      id: mech ? mech.id : null,
      designation: fd.get('designation'),
      model: fd.get('model'),
      mass: parseInt(fd.get('mass'), 10),
      tech_base: fd.get('tech_base'),
      uuid: fd.get('uuid') || null,
    };

    fetch(`${API}/api/mechs/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.detail || 'Save failed');
        onSaved({ name: payload.designation });
      })
      .catch((err) => alert('Error saving entity: ' + err.message));
  };

  return (
    <div className="bg-gray-950 p-6 rounded-lg border border-gray-800">
      <div className="flex justify-between items-center mb-6 pb-2 border-b border-gray-800">
        <h3 className="text-lg font-bold text-white">Chassis Schematic Editor</h3>
        <button
          onClick={onNewMode}
          className="text-xs px-2 py-1 bg-gray-900 border border-gray-700 hover:bg-gray-800 rounded text-amber-500"
        >
          + Force Blank Create Mode
        </button>
      </div>

      {/* keyed on mech id so defaultValues reset when switching mechs */}
      <form key={mech?.id ?? 'new'} onSubmit={handleSubmit}>
        <div className="space-y-4 text-sm">
          <LabeledInput name="designation" label="Chassis Designation" defaultValue={mech?.name || ''} required />
          <LabeledInput name="model" label="Variant Model" defaultValue={mech?.model || 'Prime'} />

          <div className="grid grid-cols-2 gap-4">
            <LabeledInput
              name="mass"
              label="Weight (Tons)"
              type="number"
              min="20"
              max="100"
              defaultValue={mech?.tonnage || 50}
              required
            />
            <div>
              <label className="block text-xs uppercase text-gray-400 mb-1">Tech Base</label>
              <select
                name="tech_base"
                defaultValue={mech?.tech_base || 'clan'}
                className="w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white focus:outline-none focus:border-amber-500"
              >
                <option value="clan">Clan Array</option>
                <option value="is">Inner Sphere Blueprint</option>
                <option value="mixed">Mixed Tech</option>
              </select>
            </div>
          </div>

          <LabeledInput
            name="uuid"
            label="Signature UUID"
            defaultValue={mech?.uuid || ''}
            className="font-mono text-xs"
          />

          <button
            type="submit"
            className="w-full py-2 bg-amber-600 hover:bg-amber-700 font-bold rounded text-white mt-4 cursor-pointer transition-colors shadow-md"
          >
            {mech ? '💾 Overwrite Active Blueprint' : '🛠️ Compile New Unit Row'}
          </button>
        </div>
      </form>
    </div>
  );
}
