// Plain, scrollable, text-only log of EVERY detail of every shot in a set of
// events: to-hit roll + target number + modifiers, hit location, cluster rolls
// and per-cluster breakdown, crits, jams, damage, heat. No fancy UI — just a
// complete monospace dump so nothing that happened is hidden.

function fmtMod(v) {
  if (v == null) return '0';
  return v > 0 ? `+${v}` : String(v);
}

// Build the flat list of text lines for one resolved fire event payload.
function shotLines(payload) {
  const lines = [];
  const header = [
    payload.attacker || 'Unknown',
    payload.target ? `→ ${payload.target}` : '(no target)',
  ].join(' ');
  lines.push(header);
  lines.push(
    `  summary: ${payload.hits ?? 0} hit / ${payload.misses ?? 0} miss · ` +
    `${payload.total_damage ?? 0} dmg · ${payload.total_heat ?? 0} heat · ` +
    `TMM ${fmtMod(payload.target_movement_modifier)}`,
  );
  if (payload.unresolved_weapons?.length) {
    lines.push(`  unresolved weapons: ${payload.unresolved_weapons.join(', ')}`);
  }

  (payload.shots ?? []).forEach((s, i) => {
    const r = s.all_rolls;
    // One-line outcome summary per shot.
    const outcome = s.jammed
      ? 'JAMMED'
      : s.hit
      ? `HIT (${s.damage} dmg)`
      : 'MISS';
    lines.push(
      `  [${i + 1}] ${s.weapon ?? '?'} · ${s.range_band ?? '—'} · facing ${s.target_facing ?? '—'} · ${outcome}`,
    );

    // To-hit detail.
    if (r && r.to_hit_1 != null) {
      const needed = s.target_number == null
        ? 'out of range'
        : s.target_number <= 2
        ? 'auto-hit'
        : `need ${s.target_number}+`;
      lines.push(
        `       to-hit: ${r.to_hit_1}+${r.to_hit_2} = ${s.roll} vs ${needed}`,
      );
    } else if (s.target_number == null) {
      lines.push('       to-hit: target out of range');
    }

    // Target-number breakdown (GATOR). The itemized components come from the
    // backend; any remainder vs the final target number (TC, pulse, etc.) is
    // shown as a single reconciling "other adjustments" line.
    const b = s.modifier_breakdown;
    if (b && s.target_number != null) {
      const parts = [
        `gunnery ${b.gunnery}`,
        `atk-move ${fmtMod(b.attacker_movement)}`,
        `tgt-move ${fmtMod(b.target_movement)}`,
        `other ${fmtMod(b.additional)}`,
        `range ${fmtMod(b.range)}${b.range_band ? ` (${b.range_band})` : ''}`,
      ];
      lines.push(`       target#: ${parts.join(' · ')}`);

      const gatorSum =
        b.gunnery + b.attacker_movement + b.target_movement + b.additional + b.range;

      // Targeting computer: call it out explicitly when the mech has one.
      const tc = b.targeting_computer || 0;
      if (b.has_targeting_computer) {
        if (tc !== 0) {
          lines.push(`                + targeting computer ${fmtMod(tc)}`);
        } else {
          lines.push('                + targeting computer (equipped, not eligible for this weapon)');
        }
      }

      // Anything still unaccounted for (e.g. pulse band modifier) folds into a
      // reconciling line so the itemized values always sum to the target number.
      const other = s.target_number - gatorSum - tc;
      if (other !== 0) {
        lines.push(`                + other adjustments ${fmtMod(other)} (e.g. pulse)`);
      }
      lines.push(`                = ${s.target_number} needed`);
    }

    // Single-location hit detail (non-cluster).
    if (s.hit && !s.cluster_hits && s.hit_location) {
      let loc = `       location: ${s.hit_location}`;
      if (r && r.location_1 != null) loc += ` (rolled ${r.location_1}+${r.location_2} = ${r.location_1 + r.location_2})`;
      if (s.critical_hit) loc += ' ✶ CRIT';
      lines.push(loc);
    }

    // Through-armor-crit reroll detail.
    if (r && r.tac_reroll_1 != null) {
      lines.push(
        `       TAC reroll: ${r.tac_reroll_1}+${r.tac_reroll_2} = ${r.tac_reroll_1 + r.tac_reroll_2}`,
      );
    }

    // Cluster detail: the cluster-table roll + each submunition group.
    if (s.cluster_roll != null) {
      lines.push(
        `       cluster: rolled ${s.cluster_roll} → ${s.cluster_hits_landed} landed`,
      );
      (s.cluster_hits ?? []).forEach((h, j) => {
        lines.push(
          `         (${j + 1}) ${h.damage} → ${h.location}${h.critical_hit ? ' ✶ CRIT' : ''}`,
        );
      });
    }
  });

  return lines;
}

export function TurnDetailLog({ turn, events, unitName }) {
  const lines = [];
  lines.push(`===== TURN ${turn} =====`);
  (events ?? []).forEach((e) => {
    lines.push('');
    lines.push(`[event #${e.id} · ${e.event_type}]`);
    if (e.payload) {
      shotLines(e.payload).forEach((l) => lines.push(l));
    } else {
      lines.push(`  ${e.attacker || unitName?.(e.session_mech_id) || 'Unknown'}`);
    }
  });

  return (
    <pre className="whitespace-pre-wrap break-words font-mono text-xs text-gray-300 bg-gray-950 border border-gray-800 rounded-lg p-4 overflow-x-auto">
      {lines.join('\n')}
    </pre>
  );
}
