// Small presentational pieces for Alpha Strike combat.

// A pip/segment bar for armor or structure. `current` of `max` filled.
// `size` controls the label text, pip size, and count readout: "sm" (default,
// compact) or "lg" (prominent, for the mech sheet).
export function ArmorBar({ label, current, max, color, size = 'sm' }) {
  const safeMax = Math.max(max || 0, current || 0, 1);
  const pips = Array.from({ length: safeMax }, (_, i) => i < (current || 0));
  const lg = size === 'lg';
  const labelCls = lg
    ? 'w-24 shrink-0 text-sm uppercase tracking-wider font-bold text-gray-300'
    : 'w-16 shrink-0 text-[10px] uppercase tracking-wider text-gray-400';
  const pipCls = lg ? 'w-5 h-5 rounded' : 'w-2.5 h-2.5 rounded-sm';
  const countCls = lg
    ? 'text-xl font-mono font-bold text-gray-100 shrink-0'
    : 'text-xs font-mono text-gray-300 shrink-0';
  return (
    <div className={`flex items-center ${lg ? 'gap-3' : 'gap-2'}`}>
      <span className={labelCls}>{label}</span>
      <div className={`flex flex-wrap ${lg ? 'gap-1' : 'gap-0.5'}`}>
        {pips.map((filled, i) => (
          <span
            key={i}
            className={`${pipCls} ${filled ? color : 'bg-gray-800 border border-gray-700'}`}
          />
        ))}
      </div>
      <span className={countCls}>
        {current ?? 0}/{max ?? 0}
      </span>
    </div>
  );
}

// Renders one resolved Alpha Strike attack (rolls, damage, armor/structure delta).
export function AsAttackResultView({ result }) {
  if (!result) return null;
  const oor = result.target_number == null;
  return (
    <div className="text-xs space-y-1.5">
      {result.target && (
        <div className="text-sm text-gray-300">
          Target: <span className="text-red-400 font-bold">{result.target}</span>
        </div>
      )}
      <div className="text-gray-400 font-mono">
        {oor ? (
          'Out of range'
        ) : (
          <>
            {result.range_band} · need {result.target_number}+ ·{' '}
            <span className="text-amber-400">{result.mode}</span>
          </>
        )}
      </div>

      {!oor && (
        <>
          {/* Every 2d6 roll: one in standard mode, one per point of bracket
              damage in variable mode. Each pair shows both dice + their total,
              green when it met the target number. */}
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-gray-500 uppercase text-[10px] mr-1 w-full sm:w-auto">Rolls</span>
            {(result.roll_pairs ?? []).map(([d1, d2], i) => {
              const total = d1 + d2;
              const met = total >= result.target_number;
              return (
                <span
                  key={i}
                  className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-mono border ${
                    met
                      ? 'bg-green-900/50 text-green-300 border-green-800'
                      : 'bg-gray-900 text-gray-500 border-gray-700'
                  }`}
                >
                  <span>{d1}</span>
                  <span className="opacity-50">+</span>
                  <span>{d2}</span>
                  <span className="opacity-50">=</span>
                  <span className="font-bold">{total}</span>
                </span>
              );
            })}
            {(result.roll_pairs ?? []).length === 0 && (
              <span className="text-gray-600 italic">none</span>
            )}
          </div>

          <div
            className={`font-bold ${result.damage_dealt > 0 ? 'text-green-400' : 'text-red-400'}`}
          >
            {result.damage_dealt > 0
              ? `${result.damage_dealt} damage (of ${result.bracket_damage} possible)`
              : 'Missed — 0 damage'}
          </div>
        </>
      )}

      {/* Armor/structure change on the target. */}
      {result.target_armor_before != null && (
        <div className="text-gray-400 font-mono">
          Armor {result.target_armor_before} → {result.target_armor_after} · Structure{' '}
          {result.target_structure_before} → {result.target_structure_after}
        </div>
      )}
    </div>
  );
}
