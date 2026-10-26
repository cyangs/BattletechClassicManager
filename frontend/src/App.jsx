import { useState } from 'react';

import MechDashboard from './features/dashboard/MechDashboard';
import { SplashScreen } from './features/splash/SplashScreen';
import AlphaStrikeApp from './features/alphastrike/AlphaStrikeApp';

function App() {
  // null = splash screen; 'classic' / 'alphastrike' = chosen game system.
  const [mode, setMode] = useState(null);

  if (mode === 'classic') {
    return <MechDashboard onExit={() => setMode(null)} />;
  }
  if (mode === 'alphastrike') {
    return <AlphaStrikeApp onExit={() => setMode(null)} />;
  }
  return <SplashScreen onSelectMode={setMode} />;
}

export default App;
