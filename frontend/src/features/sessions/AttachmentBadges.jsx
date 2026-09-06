// Little badges for the chassis-level attachments fitted onto a mech. Click a
// badge to toggle its destroyed state (combat damage) for the session.
export function AttachmentBadges({ attachments, onToggle }) {
  const list = attachments ?? [];
  if (list.length === 0) return null;
  return (
    <div className="mt-3 flex flex-wrap gap-1.5">
      {list.map((a) => {
        const destroyed = a.destroyed;
        return (
          <button
            key={a.id ?? a.sku}
            type="button"
            onClick={onToggle ? () => onToggle(a) : undefined}
            title={destroyed ? `${a.display_name} — destroyed (click to repair)` : `${a.display_name} (click to mark destroyed)`}
            className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold border ${
              destroyed
                ? 'bg-red-950/60 text-red-400 border-red-800 line-through'
                : 'bg-amber-950/50 text-amber-400 border-amber-900 hover:border-amber-600'
            }`}
          >
            {a.display_name}
          </button>
        );
      })}
    </div>
  );
}
