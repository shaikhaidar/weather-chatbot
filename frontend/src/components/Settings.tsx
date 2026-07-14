import React from 'react';
import { Settings as SettingsIcon, Server, Database, Activity, Shield } from 'lucide-react';

const Settings = ({ systemMode, setSystemMode }: { systemMode: string, setSystemMode: (mode: string) => void }) => {
  return (
    <div className="space-y-6 animate-in fade-in duration-500 max-w-4xl mx-auto">
      
      {/* Settings Header */}
      <div className="bg-white rounded-xl border shadow-sm p-6 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <SettingsIcon className="w-6 h-6 text-blue-500" />
            AI Edge Settings
          </h2>
          <p className="text-sm text-gray-500 mt-1">Configure weatherBOT behavior and security.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* System Mode Selector */}
        <div className="bg-white rounded-xl border shadow-sm p-6 space-y-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Activity className="w-5 h-5 text-indigo-500" />
            System Mode
          </h3>
          <p className="text-sm text-gray-500">
            Select how the AI should fuse data streams for inference.
          </p>
          <div className="space-y-3">
            {[
              { id: "Historical Data Mode", desc: "Ignore live edge stations. Focus entirely on CSV uploaded datasets." },
              { id: "Live Station Mode", desc: "Ignore historical CSV data. Use GNN to map spatial edge sensor telemtry." },
              { id: "Prime", desc: "Ultimate Hybrid. Fuse historical CSV and live Edge GNN inputs." }
            ].map(mode => (
              <label key={mode.id} className={`flex items-start p-4 border rounded-lg cursor-pointer transition-colors ${systemMode === mode.id ? 'bg-blue-50 border-blue-200' : 'hover:bg-gray-50'}`}>
                <input 
                  type="radio" 
                  name="system_mode" 
                  value={mode.id}
                  checked={systemMode === mode.id}
                  onChange={(e) => setSystemMode(e.target.value)}
                  className="mt-1 mr-3 text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <h4 className="font-medium text-gray-900">{mode.id === "Prime" ? "Prime Mode (Default)" : mode.id}</h4>
                  <p className="text-sm text-gray-500 mt-1">{mode.desc}</p>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Security Info Placeholder */}
        <div className="bg-white rounded-xl border shadow-sm p-6">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <Shield className="w-5 h-5 text-emerald-500" />
            Security & Authentication
          </h3>
          <div className="bg-emerald-50 text-emerald-700 p-4 rounded-lg text-sm border border-emerald-100 flex items-center gap-3">
             <Shield className="w-5 h-5 flex-shrink-0" />
             <p>This Edge Node is secured with JWT Authentication. Only authorized meteorologists have access.</p>
          </div>
          <div className="mt-6 space-y-3 text-sm">
             <div className="flex justify-between py-2 border-b">
               <span className="text-gray-500">Auth Standard</span>
               <span className="font-medium">JWT (JSON Web Token)</span>
             </div>
             <div className="flex justify-between py-2 border-b">
               <span className="text-gray-500">Encryption</span>
               <span className="font-medium">bcrypt</span>
             </div>
             <div className="flex justify-between py-2">
               <span className="text-gray-500">Active Session</span>
               <span className="font-medium text-green-600">Valid</span>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
