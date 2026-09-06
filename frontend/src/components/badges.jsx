// Small presentational badge primitives shared across features.

// Uses-ammo indicator for weapons.
export function AmmoBadge({ use }) {
  return (
    <span
      className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
        use
          ? 'bg-red-950/60 text-red-400 border border-red-900'
          : 'bg-green-950/60 text-green-400 border border-green-900'
      }`}
    >
      {use ? 'Uses Ammo' : 'No'}
    </span>
  );
}

// Inner Sphere vs Clan tech-base indicator.
export function TechBaseBadge({ techBase }) {
  const isClan = techBase === 'CLAN';
  return (
    <span
      className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
        isClan
          ? 'bg-sky-950/60 text-sky-400 border border-sky-900'
          : 'bg-gray-800/60 text-gray-300 border border-gray-700'
      }`}
    >
      {isClan ? 'Clan' : 'IS'}
    </span>
  );
}

// Player vs Enemy side indicator for a session unit.
export function TeamBadge({ team }) {
  const enemy = team === 'enemy';
  return (
    <span
      className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
        enemy
          ? 'bg-red-950/60 text-red-400 border border-red-900'
          : 'bg-sky-950/60 text-sky-400 border border-sky-900'
      }`}
    >
      {enemy ? 'Enemy' : 'Player'}
    </span>
  );
}
