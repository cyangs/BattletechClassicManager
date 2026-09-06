// Theoretical 2d6 outcome weights (out of 36) — the ideal bell curve overlaid
// on the actual rolls so a turn's luck is easy to eyeball.
const TWO_D6_WEIGHTS = { 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 5, 9: 4, 10: 3, 11: 2, 12: 1 };

// Pull every 2d6 total rolled across a set of fire events: to-hit rolls, hit
// location rolls, through-armor-crit rerolls, and cluster-table rolls.
export function collectTurnRolls(events) {
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
export function RollDistribution({ turn, events }) {
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
