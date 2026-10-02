import { useState } from 'react';

import { FireResults } from './FireResults';
import { RollDistribution } from './RollDistribution';
import { TurnDetailLog } from './TurnDetailLog';

// History view: the chronological log of session events, grouped by turn
// (newest turn first). Two modes: the default cards+chart summary, and a
// "Detailed Log" that dumps every roll/modifier/cluster result as plain text.
export function SessionHistory({ events, units }) {
  const unitName = (id) => units.find((u) => u.id === id)?.name;
  const [detailed, setDetailed] = useState(false);
  // Group events by turn, newest turn first; the chart for a turn sits to the
  // right of that same turn's event cards.
  const turns = [...new Set(events.map((e) => e.turn))].sort((a, b) => b - a);

  return (
    <div className="flex-1 overflow-y-auto p-6">
      <div className="mx-auto w-full max-w-7xl space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold uppercase tracking-wider text-amber-500">
            Session History
          </h2>
          <button
            onClick={() => setDetailed((v) => !v)}
            className={`px-4 py-2 rounded text-sm font-bold border transition-colors ${
              detailed
                ? 'bg-amber-950/40 border-amber-700/50 text-amber-400'
                : 'bg-gray-900 border-gray-700 text-gray-300 hover:bg-gray-800'
            }`}
          >
            📋 Detailed Log{detailed ? ' ✓' : ''}
          </button>
        </div>

        {turns.length === 0 ? (
          <div className="text-center text-gray-500 text-sm py-8">
            No events yet. Fire weapons and run turns to build the log.
          </div>
        ) : detailed ? (
          // Full text dump: every event, every roll, grouped by turn.
          turns.map((t) => (
            <TurnDetailLog
              key={t}
              turn={t}
              unitName={unitName}
              events={events.filter((e) => e.turn === t).reverse()}
            />
          ))
        ) : (
          turns.map((t) => {
            const turnEvents = events.filter((e) => e.turn === t).reverse(); // newest first within turn
            return (
              <div key={t} className="flex items-start gap-6">
                {/* Left: this turn's event log */}
                <div className="min-w-0 flex-1 space-y-3">
                  {turnEvents.map((e) => (
                    <div key={e.id} className="border border-gray-800 rounded-lg bg-gray-950 p-4">
                      <div className="flex items-center justify-between mb-2">
                        <div className="text-sm text-white font-semibold">
                          <span className="text-amber-400">Turn {e.turn}</span> ·{' '}
                          {e.attacker || unitName(e.session_mech_id) || 'Unknown'}
                          {e.target && (
                            <>
                              {' → '}
                              <span className="text-red-400">{e.target}</span>
                            </>
                          )}
                        </div>
                        <span className="text-[10px] uppercase font-bold px-2 py-0.5 rounded bg-gray-800 border border-gray-700 text-gray-400">
                          {e.event_type}
                        </span>
                      </div>
                      <FireResults result={e.payload} />
                    </div>
                  ))}
                </div>

                {/* Right: this turn's 2d6 roll distribution */}
                <div className="w-96 shrink-0">
                  <RollDistribution turn={t} events={events.filter((e) => e.turn === t)} />
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
