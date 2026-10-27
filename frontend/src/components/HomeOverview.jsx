// Shared landing/overview page shown when either app first opens. It explains
// the three building blocks (Mech Library, Weapons Library, Sessions) so a new
// player lands somewhere descriptive instead of jumping straight into a library
// or a live session. Parameterized by game system so the copy + accent colors
// match the app that renders it.
//
// Each card links to the tab it describes via the ``onNavigate(tabId)``
// callback supplied by the hosting shell (MechDashboard / AlphaStrikeApp).

const SYSTEMS = {
  classic: {
    title: 'BattleTech: Classic',
    accent: 'text-amber-400',
    ring: 'border-amber-700/40',
    hover: 'hover:border-amber-500/70 hover:bg-amber-950/10',
    focusRing: 'focus:ring-amber-500',
    chip: 'bg-amber-950/40 text-amber-300',
    blurb:
      'The full tabletop ruleset: per-location armor and structure, heat, ' +
      'cluster hits, and detailed weapon resolution.',
    sessions: {
      tab: 'sessions',
      label: '🎲 Sessions',
      text:
        'A Session is a single battle. Deploy mechs from your library onto ' +
        'teams, then resolve attacks turn by turn. Each deployed mech tracks ' +
        'its own armor, structure, and heat, and a running event log records ' +
        'every shot. Create a session from the Sessions tab (admin mode), share ' +
        'the join code, and your friends can pick a side and play along.',
    },
  },
  alpha_strike: {
    title: 'BattleTech: Alpha Strike',
    accent: 'text-sky-400',
    ring: 'border-sky-700/40',
    hover: 'hover:border-sky-500/70 hover:bg-sky-950/10',
    focusRing: 'focus:ring-sky-500',
    chip: 'bg-sky-950/40 text-sky-300',
    blurb:
      'The fast-play ruleset: single armor + structure bars, range-bracket ' +
      'damage, and streamlined to-hit — the same mechs, a quicker game.',
    sessions: {
      tab: 'games',
      label: '🎲 Alpha Strike Games',
      text:
        'A Game is a single Alpha Strike battle. Deploy mechs (using their ' +
        'Alpha Strike cards) onto teams, then trade attacks using range-bracket ' +
        'damage. Each unit tracks a single armor bar and structure bar. Create a ' +
        'game from the Games tab, share the join code, and play with friends.',
    },
  },
};

// A card that navigates to the tab it describes when clicked. Falls back to a
// plain (non-interactive) card if no navigation handler is provided.
function Card({ icon, title, children, ring, hover, accent, focusRing, onClick }) {
  const interactive = typeof onClick === 'function';
  const base = `group w-full text-left rounded-lg border ${ring} bg-gray-800/40 p-5`;

  const inner = (
    <>
      <div className="flex items-center gap-2 mb-2 text-base font-semibold text-gray-100">
        <span>{icon}</span>
        <span>{title}</span>
        {interactive && (
          <span className={`ml-auto text-sm opacity-0 group-hover:opacity-100 transition-opacity ${accent}`}>
            Open →
          </span>
        )}
      </div>
      <p className="text-sm leading-relaxed text-gray-400">{children}</p>
    </>
  );

  if (!interactive) {
    return <div className={base}>{inner}</div>;
  }

  return (
    <button
      type="button"
      onClick={onClick}
      className={`${base} ${hover} ${focusRing} transition-colors cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-900`}
    >
      {inner}
    </button>
  );
}

export default function HomeOverview({ system = 'classic', onNavigate }) {
  const cfg = SYSTEMS[system] ?? SYSTEMS.classic;
  // Build a click handler for a given tab id (or undefined if no nav handler).
  const go = (tab) => (onNavigate ? () => onNavigate(tab) : undefined);

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-3xl mx-auto px-6 py-10">
        <div className={`inline-block text-xs font-medium px-2 py-1 rounded ${cfg.chip} mb-3`}>
          Overview
        </div>
        <h1 className={`text-2xl font-bold ${cfg.accent} mb-2`}>{cfg.title}</h1>
        <p className="text-sm text-gray-400 leading-relaxed mb-8">{cfg.blurb}</p>

        <div className="grid gap-4">
          <Card
            icon="🤖"
            title="Mechs Library"
            ring={cfg.ring}
            hover={cfg.hover}
            accent={cfg.accent}
            focusRing={cfg.focusRing}
            onClick={go('mechs')}
          >
            Your roster of chassis. Every mech lives here once — its name, model
            variant, tonnage, movement, armor/structure layout, and mounted
            weapons. The same library is shared across both game systems, so a
            mech you build for Classic already carries its Alpha Strike card.
          </Card>

          <Card
            icon="⚔️"
            title="Weapons & Parts Library"
            ring={cfg.ring}
            hover={cfg.hover}
            accent={cfg.accent}
            focusRing={cfg.focusRing}
            onClick={go('weapons')}
          >
            The catalog of weapons and equipment you can mount on mechs. Each
            entry defines damage, range brackets, heat, ammo, and any special
            behavior (cluster, Ultra/LB-X/Rotary autocannons, Streak/MRM
            missiles, Heavy lasers, and more). Edit these once and every mech
            that mounts them stays in sync.
          </Card>

          <Card
            icon={cfg.sessions.label.split(' ')[0]}
            title={cfg.sessions.label.replace(/^\S+\s/, '')}
            ring={cfg.ring}
            hover={cfg.hover}
            accent={cfg.accent}
            focusRing={cfg.focusRing}
            onClick={go(cfg.sessions.tab)}
          >
            {cfg.sessions.text}
          </Card>
        </div>

        <p className="text-xs text-gray-600 mt-8">
          Pick a card or a tab above to get started.
        </p>
      </div>
    </div>
  );
}
