// Labeled text input used across the library editor forms.
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
