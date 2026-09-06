// A single d6 face rendered as a small pip box.
export function Die({ value }) {
  return (
    <span className="inline-flex items-center justify-center w-5 h-5 rounded bg-gray-800 border border-gray-600 text-gray-100 text-[10px] font-bold">
      {value}
    </span>
  );
}
