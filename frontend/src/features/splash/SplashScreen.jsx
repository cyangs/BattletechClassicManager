// Entry splash: pick a game system. Classic routes to the current manager;
// Alpha Strike is a placeholder for now. The image areas are placeholders —
// drop real art in later by replacing the gradient block in GameModeCard.

function GameModeCard({ title, subtitle, accent, image, available, onSelect }) {
  return (
    <button
      onClick={onSelect}
      className={`group relative w-96 rounded-xl border overflow-hidden text-left transition-transform hover:-translate-y-1 ${
        available
          ? 'border-amber-700/50 hover:border-amber-500'
          : 'border-gray-800 hover:border-gray-600'
      }`}
    >
      {/* Cover art. object-contain shows the whole cover; falls back to a
          gradient block if the image is missing. */}
      <div className={`h-[32rem] flex items-center justify-center bg-gradient-to-br ${accent} overflow-hidden`}>
        <img
          src={image}
          alt={title}
          className="max-h-full max-w-full object-contain"
          onError={(e) => {
            // Hide a broken image so the gradient shows through as a fallback.
            e.currentTarget.style.display = 'none';
          }}
        />
      </div>

      {/* Caption */}
      <div className="p-4 bg-gray-950">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold text-white">{title}</h2>
          {!available && (
            <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-gray-800 border border-gray-700 text-gray-400">
              Coming Soon
            </span>
          )}
        </div>
        <p className="text-sm text-gray-400 mt-1">{subtitle}</p>
      </div>
    </button>
  );
}

export function SplashScreen({ onSelectMode }) {
  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-900 text-gray-100 font-sans p-8">
      <h1 className="text-3xl font-extrabold text-amber-500 mb-2 text-center">
        Calvin's Super Awesome BattleTech Campaign Manager
      </h1>
      <p className="text-gray-400 mb-10 text-center">Choose your game system</p>

      <div className="flex flex-wrap gap-8 justify-center">
        <GameModeCard
          title="Classic BattleTech"
          subtitle="Full mech & weapon manager with turn-based combat."
          accent="from-amber-900/60 to-gray-900"
          image="/classic.jpg"
          available
          onSelect={() => onSelectMode('classic')}
        />
        <GameModeCard
          title="Alpha Strike"
          subtitle="Fast-play rules with armor/structure and bracket damage."
          accent="from-sky-900/60 to-gray-900"
          image="/alpha-strike.jpg"
          available
          onSelect={() => onSelectMode('alphastrike')}
        />
      </div>
    </div>
  );
}
