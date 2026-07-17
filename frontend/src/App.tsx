import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import RawDataset from './components/RawDataset';
import Settings from './components/Settings';
import ChatWindow from './components/ChatWindow';
import History from './components/History';
import Login from './components/Login';
import { setAuthToken } from './api';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentView, setCurrentView] = useState('Chat');
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);
  const [systemMode, setSystemMode] = useState('Prime');
  
  // Hardware connectivity status for physical IoT stations
  const [isStationConnected, setIsStationConnected] = useState(false);

  useEffect(() => {
    // Check local hardware IoT status via backend endpoint if available
    fetch('/api/predictions/iot')
      .then(res => res.json())
      .then(data => {
        if (data && data.source !== 'simulator' && data.connected) {
          setIsStationConnected(true);
        } else {
          setIsStationConnected(false);
        }
      })
      .catch(() => setIsStationConnected(false));
  }, []);

  const handleLogin = (token: string) => {
    setAuthToken(token);
    setIsAuthenticated(true);
  };

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  const handleSelectSession = (id: string) => {
    setSelectedSessionId(id);
    setCurrentView('Chat');
  };

  const handleSidebarClick = (view: string) => {
    setCurrentView(view);
  };

  return (
    <div className="flex h-screen w-full bg-gray-50 text-gray-900 font-sans overflow-hidden">
      {/* Left Sidebar */}
      <Sidebar currentView={currentView} setCurrentView={handleSidebarClick} />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Header */}
        <header className="h-14 border-b bg-white flex items-center justify-between px-6 shadow-sm z-10">
          <div className="flex items-center gap-4">
            <h1 className="text-xl font-semibold">{currentView}</h1>
            <span className="px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-700 text-xs font-semibold">{systemMode} Mode</span>
          </div>
          <div className="flex items-center gap-2 text-sm font-medium">
            <span className={`w-2.5 h-2.5 rounded-full ${isStationConnected ? 'bg-green-500' : 'bg-red-500'}`}></span>
            {isStationConnected ? (
              <span className="text-green-600">Hardware Connected (Serial/MQTT)</span>
            ) : (
              <span className="text-red-500">Hardware Disconnected (Historical ML Mode)</span>
            )}
          </div>
        </header>

        {/* Content Body */}
        <main className="flex-1 overflow-y-auto p-6 bg-gray-50">
          {currentView === 'Chat' && (
            <ChatWindow 
              sessionIdProp={selectedSessionId} 
              systemMode={systemMode} 
              onSessionInit={(id) => setSelectedSessionId(id)}
            />
          )}
          {currentView === 'Raw Dataset' && <RawDataset />}
          {currentView === 'Conversation History' && <History onSelectSession={handleSelectSession} />}
          {currentView === 'Settings' && <Settings systemMode={systemMode} setSystemMode={setSystemMode} />}
        </main>
      </div>
    </div>
  );
}

export default App;
