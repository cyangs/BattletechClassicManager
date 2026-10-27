import { useState } from 'react';

// Renders one drawn Aces AI control card beside a unit. The card is pure
// reference text — movement phase (optional "if first" + three postures) and
// combat phase (target hierarchy + overheat + specials). The GM reads the board
// and picks the posture; it defaults to Cautious.

const POSTURES = [
  { id: 'aggressive', label: 'Aggressive', accent: 'text-red-400', ring: 'border-red-700/50', active: 'bg-red-950/40' },
  { id: 'balanced', label: 'Balanced', accent: 'text-amber-400', ring: 'border-amber-700/50', active: 'bg-amber-950/40' },
  { id: 'cautious', label: 'Cautious', accent: 'text-sky-400', ring: 'border-sky-700/50', active: 'bg-sky-950/40' },
];

// When ``embedded`` is true, the card drops its own border + header and the
// Draw/Clear controls (the parent container owns all of that) and fills the
// available height so it matches the mech card beside it.
export function AiControlCard({ card, onReroll, onClear, embedded = false }) {
  // Posture defaults to Cautious per the GM's workflow.
  const [posture, setPosture] = useState('cautious');

  if (!card) return null;

  const movement = card.movement ?? {};
  const postures = movement.postures ?? {};
  const active = postures[posture] ?? {};
  const combat = card.combat ?? {};
  const activeMeta = POSTURES.find((p) => p.id === posture) ?? POSTURES[2];

  return (
    <div
      className={
        embedded
          ? 'bg-sky-950/10 w-full h-full flex flex-col'
          : 'border border-sky-900/60 rounded-lg bg-sky-950/10 w-full overflow-hidden self-start'
      }
    >
      {/* Header — parent owns it in embedded mode, so show a compact variant. */}
      <div className="flex items-center gap-2 px-4 py-2 border-b border-sky-900/40 bg-sky-950/20">
        <span className="text-sky-400">🧠</span>
        <span className="text-sm font-bold text-sky-300 uppercase tracking-wide truncate">
          {card.role} AI
        </span>
        {card.card_number && (
          <span className="text-[10px] text-gray-500 font-mono shrink-0">#{card.card_number}</span>
        )}
        {card.activation_number != null && (
          <span className="ml-auto text-[10px] text-gray-500 font-mono shrink-0">
            ACT {card.activation_number}
          </span>
        )}
      </div>

      <div className="p-4 space-y-4">
        {/* Posture selector — pick based on board conditions (default Cautious). */}
        <div>
          <div className="text-[10px] uppercase tracking-wider text-gray-400 mb-1.5 font-bold">
            Posture — pick the first whose condition is true
          </div>
          <div className="grid grid-cols-3 gap-1.5">
            {POSTURES.map((p) => {
              const selected = posture === p.id;
              return (
                <button
                  key={p.id}
                  onClick={() => setPosture(p.id)}
                  className={`px-2 py-1 rounded text-[11px] font-bold border transition-colors ${
                    selected
                      ? `${p.active} ${p.ring} ${p.accent}`
                      : 'border-gray-700 text-gray-400 hover:text-white hover:bg-gray-900'
                  }`}
                >
                  {p.label}
                </button>
              );
            })}
          </div>
          {/* Condition lines for all three so the GM can compare. */}
          <div className="mt-2 space-y-1">
            {POSTURES.map((p) => {
              const cond = postures[p.id]?.condition;
              if (!cond) return null;
              const selected = posture === p.id;
              return (
                <div
                  key={p.id}
                  className={`text-[11px] leading-snug ${
                    selected ? `${p.accent} font-medium` : 'text-gray-500'
                  }`}
                >
                  <span className="uppercase font-bold">{p.label}:</span> {cond}
                </div>
              );
            })}
          </div>
        </div>

        {/* MOVEMENT PHASE */}
        <Section title="Movement Phase" accent="text-sky-400/90">
          {movement.if_first && (
            <div className="mb-2 rounded border border-amber-800/40 bg-amber-950/20 p-2">
              <div className="text-[10px] uppercase font-bold text-amber-400/90 mb-0.5">
                If First to Move (lost initiative)
              </div>
              {movement.if_first.trigger && (
                <p className="text-[11px] italic text-gray-500 mb-1">{movement.if_first.trigger}</p>
              )}
              <p className="text-xs text-gray-300 leading-relaxed">{movement.if_first.action}</p>
            </div>
          )}

          <div className={`rounded border ${activeMeta.ring} ${activeMeta.active} p-2`}>
            <div className={`text-[10px] uppercase font-bold mb-1 ${activeMeta.accent}`}>
              {activeMeta.label} — Movement Filters
            </div>
            {active.condition && (
              <p className="text-[11px] italic text-gray-400 mb-1.5">{active.condition}</p>
            )}
            <ol className="list-decimal list-inside space-y-1 text-xs text-gray-300 leading-relaxed">
              {(active.filters ?? []).map((f, i) => (
                <li key={i}>{f}</li>
              ))}
            </ol>
          </div>
        </Section>

        {/* COMBAT PHASE */}
        <Section title="Combat Phase" accent="text-red-400/90">
          {Array.isArray(combat.target_selection) && combat.target_selection.length > 0 && (
            <div className="mb-2">
              <div className="text-[10px] uppercase font-bold text-gray-400 mb-1">
                Target Selection (top to bottom)
              </div>
              <ol className="list-decimal list-inside space-y-1 text-xs text-gray-300 leading-relaxed">
                {combat.target_selection.map((t, i) => (
                  <li key={i}>{t}</li>
                ))}
              </ol>
            </div>
          )}
          {combat.overheat && (
            <div className="mb-2">
              <div className="text-[10px] uppercase font-bold text-orange-400/90 mb-0.5">
                Overheat (OV)
              </div>
              <p className="text-xs text-gray-300 leading-relaxed">{combat.overheat}</p>
            </div>
          )}
          {Array.isArray(combat.special) && combat.special.length > 0 && (
            <div>
              <div className="text-[10px] uppercase font-bold text-gray-400 mb-1">Special</div>
              <ul className="list-disc list-inside space-y-1 text-xs text-gray-300 leading-relaxed">
                {combat.special.map((s, i) => (
                  <li key={i}>{s}</li>
                ))}
              </ul>
            </div>
          )}
        </Section>

        {/* Controls — only in standalone mode; the parent container owns the
            Draw/Clear controls when embedded. */}
        {!embedded && (
          <div className="flex gap-2 pt-1">
            <button
              onClick={onReroll}
              className="flex-1 px-3 py-1.5 bg-sky-800/60 hover:bg-sky-700/60 border border-sky-700/50 rounded text-sky-200 text-xs font-bold"
            >
              🎲 Draw Another
            </button>
            <button
              onClick={onClear}
              className="px-3 py-1.5 bg-gray-800 hover:bg-gray-700 border border-gray-700 rounded text-gray-300 text-xs font-bold"
            >
              Clear
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

function Section({ title, accent, children }) {
  return (
    <div>
      <div className={`text-xs font-bold uppercase tracking-wider mb-1.5 ${accent}`}>{title}</div>
      {children}
    </div>
  );
}
