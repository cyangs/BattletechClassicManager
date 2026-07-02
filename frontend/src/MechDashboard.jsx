import { useState, useEffect, useCallback } from 'react';

const API = 'http://localhost:8000';

const TABS = [
  { id: 'mechs', label: '🤖 Mechs Library' },
  { id: 'weapons', label: '⚔️ Weapons Library' },
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
          BattleTech Classic Manager
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

// =====================================================================
// TAB 1: MECHS LIBRARY — roster sidebar + overview / weapons / editor
// =====================================================================
function MechsLibrary({ mechs, weapons, reload }) {
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
                <div className="font-semibold text-white">{mech.name}</div>
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
                <MechOverview mech={selectedMech} />
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

const MECH_LOCATIONS = [
  'Head',
  'Center Torso',
  'Left Torso',
  'Right Torso',
  'Left Arm',
  'Right Arm',
  'Left Leg',
  'Right Leg',
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

function AmmoBadge({ use }) {
  return (
    <span
      className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
        use
          ? 'bg-red-950/60 text-red-400 border border-red-900'
          : 'bg-green-950/60 text-green-400 border border-green-900'
      }`}
    >
      {use ? 'Yes' : 'No'}
    </span>
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

function LabeledInput({ label, className = '', ...props }) {
  return (
    <div>
      <label className="block text-xs uppercase text-gray-400 mb-1">{label}</label>
      <input
        {...props}
        className={`w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white focus:outline-none focus:border-amber-500 ${className}`}
      />
    </div>
  );
}

// =====================================================================
// TAB 2: WEAPONS LIBRARY — read-only weapons_master catalog
// =====================================================================
function WeaponsLibrary({ weapons, reload }) {
  const [query, setQuery] = useState('');
  // null = closed, {} = new weapon, weapon object = editing that weapon
  const [editing, setEditing] = useState(null);
  const filtered = weapons.filter((w) =>
    `${w.full_name || ''} ${w.name}`.toLowerCase().includes(query.toLowerCase()),
  );

  return (
    <div className="h-full overflow-y-auto p-8">
      <div className="max-w-5xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-amber-500">Weapons Master Catalog</h1>
          <div className="flex gap-3">
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
        </div>

        <div className="border border-gray-800 rounded-lg bg-gray-950 overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-900 text-gray-400 text-xs uppercase">
              <tr>
                <th className="px-6 py-3">Weapon System</th>
                <th className="px-4 py-3">Damage</th>
                <th className="px-4 py-3">Heat</th>
                <th className="px-4 py-3">Ammo</th>
                <th className="px-4 py-3">Range (min / S / M / L)</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-800 text-gray-300">
              {filtered.map((w) => (
                <tr key={w.id} className="hover:bg-gray-900/20">
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
                  <td colSpan="6" className="px-6 py-8 text-center text-gray-500">
                    No weapons in the catalog match your filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
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
    </div>
  );
}

function WeaponEditor({ weapon, onClose, onSaved }) {
  const handleSubmit = (e) => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const num = (v) => (v === '' || v == null ? null : parseInt(v, 10));
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
            <LabeledInput name="damage" label="Damage" type="number" min="0" defaultValue={weapon?.damage ?? 0} required />
            <LabeledInput name="heat" label="Heat" type="number" min="0" defaultValue={weapon?.heat ?? 0} required />
          </div>

          <div className="grid grid-cols-4 gap-3">
            <LabeledInput name="minimum_range" label="Min Rng" type="number" min="0" defaultValue={weapon?.minimum_range ?? ''} />
            <LabeledInput name="short_range" label="Short" type="number" min="0" defaultValue={weapon?.short_range ?? ''} />
            <LabeledInput name="medium_range" label="Medium" type="number" min="0" defaultValue={weapon?.medium_range ?? ''} />
            <LabeledInput name="long_range" label="Long" type="number" min="0" defaultValue={weapon?.long_range ?? ''} />
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

// =====================================================================
// TAB 3: SESSIONS — game rooms with deployed mech rosters
// =====================================================================
function Sessions({ sessions, mechs, reload }) {
  const [selectedId, setSelectedId] = useState(sessions[0]?.id ?? null);
  const [newName, setNewName] = useState('');
  const [mechToAdd, setMechToAdd] = useState('');

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
      body: JSON.stringify({ mech_ids: [parseInt(mechToAdd, 10)] }),
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

  const inProgress = selected?.status === 'in_progress';

  return (
    <div className="flex h-full">
      {/* LEFT: session list + create */}
      <div className="w-80 border-r border-gray-800 bg-gray-950 flex flex-col shrink-0">
        <div className="p-4 border-b border-gray-800">
          <h1 className="text-lg font-bold text-amber-500 mb-3">Game Sessions</h1>
          <form onSubmit={createSession} className="flex gap-2">
            <input
              type="text"
              placeholder="New session name..."
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="flex-1 px-3 py-2 bg-gray-900 border border-gray-700 rounded text-sm text-white focus:outline-none focus:border-amber-500"
            />
            <button
              type="submit"
              className="px-3 py-2 bg-amber-600 hover:bg-amber-700 rounded text-white text-sm font-bold"
            >
              +
            </button>
          </form>
        </div>

        <div className="flex-1 overflow-y-auto">
          {sessions.map((s) => (
            <button
              key={s.id}
              onClick={() => setSelectedId(s.id)}
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
                {inProgress ? (
                  <button
                    onClick={runTurn}
                    className="px-5 py-2.5 bg-amber-600 hover:bg-amber-500 rounded text-white font-bold shadow-md"
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
                  onClick={() => deleteSession(selected.id)}
                  className="text-xs px-3 py-1.5 bg-red-950/60 border border-red-900 hover:bg-red-900/60 rounded text-red-400"
                >
                  Delete
                </button>
              </div>
            </div>

            {/* Body: lobby (build roster) vs in-progress (combat) */}
            {inProgress ? (
              <div className="flex-1 p-6 overflow-y-auto max-w-5xl w-full mx-auto space-y-4">
                {selected.mechs.map((unit) => (
                  <SessionMechRow
                    key={unit.id}
                    sessionId={selected.id}
                    unit={unit}
                    mech={mechs.find((m) => m.id === unit.mech_id)}
                  />
                ))}
              </div>
            ) : (
              <div className="flex-1 p-8 overflow-y-auto max-w-3xl w-full mx-auto space-y-6">
                {/* Add a mech */}
                <div className="bg-gray-950 p-4 rounded-lg border border-gray-800 flex gap-3 items-end">
                  <div className="flex-1">
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
                        <th className="px-4 py-3">Tonnage</th>
                        <th className="px-4 py-3">Tech</th>
                        <th className="px-4 py-3"></th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-800 text-gray-300">
                      {selected.mechs.map((unit) => (
                        <tr key={unit.id} className="hover:bg-gray-900/20">
                          <td className="px-6 py-4 text-white font-medium">{unit.name}</td>
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
                          <td colSpan="4" className="px-6 py-8 text-center text-gray-500">
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
function SessionMechRow({ sessionId, unit, mech }) {
  const links = mech?.weapon_links ?? [];
  const [selected, setSelected] = useState(() => new Set());
  const [result, setResult] = useState(null);
  const [firing, setFiring] = useState(false);

  const toggle = (id) =>
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });

  const fire = () => {
    setFiring(true);
    fetch(`${API}/api/sessions/${sessionId}/fire`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mech_id: unit.mech_id, weapon_link_ids: [...selected] }),
    })
      .then(async (res) => {
        const body = await res.json();
        if (!res.ok) throw new Error(body.detail || 'Fire failed');
        setResult(body);
      })
      .catch((err) => alert('Error firing weapons: ' + err.message))
      .finally(() => setFiring(false));
  };

  return (
    <div className="border border-gray-800 rounded-lg bg-gray-950 p-4 flex gap-4">
      {/* Left: mech + selectable weapons */}
      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-center mb-3">
          <div className="text-white font-bold">{unit.name}</div>
          <span className="text-xs text-gray-500 font-mono uppercase">
            {unit.tonnage ?? '—'}t · {unit.tech_base ?? '—'}
          </span>
        </div>

        {links.length === 0 ? (
          <div className="text-xs text-gray-500">No weapons mounted on this chassis.</div>
        ) : (
          <div className="space-y-1.5">
            {links.map((link) => (
              <label
                key={link.id}
                className="flex items-center gap-2 text-sm text-gray-300 cursor-pointer"
              >
                <input
                  type="checkbox"
                  checked={selected.has(link.id)}
                  onChange={() => toggle(link.id)}
                  className="w-4 h-4 accent-amber-600"
                />
                <span className="text-amber-500 font-bold">{link.count}x</span>
                <span className="truncate">{link.weapon?.full_name || link.weapon?.name}</span>
                <span className="text-xs text-gray-500 font-mono">· {link.location}</span>
              </label>
            ))}
          </div>
        )}

        <button
          onClick={fire}
          disabled={selected.size === 0 || firing}
          className="mt-4 px-4 py-2 bg-red-700 hover:bg-red-600 rounded text-white text-sm font-bold uppercase tracking-wide disabled:opacity-40 disabled:cursor-not-allowed"
        >
          🔥 Fire Weapons
        </button>
      </div>

      {/* Right: fire results */}
      <div className="w-64 shrink-0 border-l border-gray-800 pl-4">
        {result ? (
          <FireResults result={result} />
        ) : (
          <div className="text-xs text-gray-600 italic">No fire resolved yet.</div>
        )}
      </div>
    </div>
  );
}

function FireResults({ result }) {
  return (
    <div className="text-xs space-y-2">
      <div className="text-gray-400">
        Turn {result.turn} ·{' '}
        <span className="text-green-400">{result.hits} hit</span> /{' '}
        <span className="text-red-400">{result.misses} miss</span>
      </div>
      <div className="space-y-1">
        {result.shots.map((s, i) => (
          <div
            key={i}
            className={`flex justify-between gap-2 font-mono ${s.hit ? 'text-gray-200' : 'text-gray-500'}`}
          >
            <span className="truncate">{s.weapon}</span>
            <span className="shrink-0">{s.hit ? `HIT ${s.damage}` : `miss (${s.roll})`}</span>
          </div>
        ))}
      </div>
      <div className="pt-1.5 border-t border-gray-800 text-amber-400 font-bold">
        {result.total_damage} dmg · {result.total_heat} heat
      </div>
    </div>
  );
}
