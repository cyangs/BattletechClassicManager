// Summarizes a fire result as total damage dealt to each of the target's
// locations (hits only), most-damaged first.
export function DamageByLocation({ result }) {
  const byLocation = {};
  (result.shots ?? []).forEach((s) => {
    if (!s.hit) return;
    if (s.cluster_hits) {
      // Cluster weapon: each cluster landed its own damage on its own location.
      s.cluster_hits.forEach((h) => {
        byLocation[h.location] = (byLocation[h.location] || 0) + (h.damage || 0);
      });
    } else if (s.hit_location) {
      byLocation[s.hit_location] = (byLocation[s.hit_location] || 0) + (s.damage || 0);
    }
  });
  const rows = Object.entries(byLocation).sort((a, b) => b[1] - a[1]);
  const total = rows.reduce((sum, [, dmg]) => sum + dmg, 0);

  return (
    <div className="text-base space-y-2 text-right">
      <div className="text-large font-bold uppercase tracking-wider text-amber-500/80">
        Damage by Location
      </div>
      {rows.length === 0 ? (
        <div className="text-gray-600 italic">No damage dealt.</div>
      ) : (
        <>
          <div className="space-y-1">
            {rows.map(([location, dmg]) => (
              <div
                key={location}
                className="flex items-center justify-end gap-2 rounded border border-gray-800 bg-gray-900/40 px-2 py-1"
              >
                <span className="truncate text-gray-200">{location}</span>
                <span className="shrink-0 font-bold text-amber-400">{dmg}</span>
              </div>
            ))}
          </div>
          <div className="flex items-center justify-end gap-2 border-t border-gray-800 pt-1.5 font-bold text-amber-400">
            <span>Total</span>
            <span>{total}</span>
          </div>
        </>
      )}
    </div>
  );
}
