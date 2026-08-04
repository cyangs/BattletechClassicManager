// Small presentational primitives shared by the Mechs and Weapons libraries.

export function LabeledInput({ label, className = '', ...props }) {
  return (
    <div>
      <label className="block text-xs uppercase text-gray-400 mb-1">{label}</label>
      <input
        {...props}
        className={`w-full px-3 py-2 bg-gray-900 border border-gray-700 rounded text-white focus:outline-none focus:border-amber-500 ${className}`}
      />
    </div>
  );
}

export function AmmoBadge({ use }) {
  return (
    <span
      className={`px-2 py-0.5 rounded text-[10px] uppercase font-bold ${
        use
          ? 'bg-red-950/60 text-red-400 border border-red-900'
          : 'bg-green-950/60 text-green-400 border border-green-900'
      }`}
    >
      {use ? 'Yes' : 'No'}
    </span>
  );
}
