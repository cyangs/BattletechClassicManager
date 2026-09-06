import { Die } from '../../components/Die';

// Renders the resolved shots for one fire event: per-shot outcome, hit
// location(s), and the individual 2d6 rolls that produced them.
export function FireResults({ result }) {
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
