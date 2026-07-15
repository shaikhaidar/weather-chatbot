import { useState, useEffect } from 'react';
import { Settings as SettingsIcon, Activity, Shield, Wifi, WifiOff, Cpu, Zap, RefreshCw } from 'lucide-react';
import { getIoTStatus, getIoTReading, getMCPTools, connectSerial, connectMQTT } from '../api';

interface IoTStatus {
  connected: boolean;
  source: string;
  last_reading_at: string;
  serial_available: boolean;
  mqtt_available: boolean;
}

interface IoTReading {
  temperature?: number;
  humidity?: number;
  pressure?: number;
  wind_speed?: number;
  rainfall?: number;
  light_intensity?: number;
  source?: string;
  timestamp?: string;
}

const Settings = ({ systemMode, setSystemMode }: { systemMode: string; setSystemMode: (mode: string) => void }) => {
  const [iotStatus, setIoTStatus] = useState<IoTStatus | null>(null);
  const [iotReading, setIoTReading] = useState<IoTReading | null>(null);
  const [mcpTools, setMcpTools] = useState<any>(null);
  const [serialPort, setSerialPort] = useState('COM3');
  const [serialBaud, setSerialBaud] = useState(9600);
  const [mqttHost, setMqttHost] = useState('192.168.1.100');
  const [mqttPort, setMqttPort] = useState(1883);
  const [connecting, setConnecting] = useState(false);
  const [connectMsg, setConnectMsg] = useState('');

  const fetchStatus = async () => {
    try {
      const [status, reading, tools] = await Promise.all([
        getIoTStatus(),
        getIoTReading(),
        getMCPTools(),
      ]);
      setIoTStatus(status);
      setIoTReading(reading);
      setMcpTools(tools);
    } catch (e) {
      console.error('Failed to fetch IoT/MCP status', e);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  const handleConnectSerial = async () => {
    setConnecting(true);
    try {
      const result = await connectSerial(serialPort, serialBaud);
      setConnectMsg(`✅ ${result.status} on ${serialPort}`);
      await fetchStatus();
    } catch {
      setConnectMsg('❌ Serial connection failed');
    }
    setConnecting(false);
  };

  const handleConnectMQTT = async () => {
    setConnecting(true);
    try {
      const result = await connectMQTT(mqttHost, mqttPort);
      setConnectMsg(`✅ MQTT ${result.status} to ${mqttHost}`);
      await fetchStatus();
    } catch {
      setConnectMsg('❌ MQTT connection failed');
    }
    setConnecting(false);
  };

  const sourceLabel: Record<string, string> = {
    serial: 'Raspberry Pi (USB Serial)',
    mqtt: 'MQTT Broker (Wi-Fi)',
    simulator: 'IoT Simulator',
  };

  return (
    <div className="space-y-6 animate-in fade-in duration-500 max-w-4xl mx-auto">

      {/* Header */}
      <div className="bg-white rounded-xl border shadow-sm p-6 flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold flex items-center gap-2">
            <SettingsIcon className="w-6 h-6 text-blue-500" />
            AI Edge Settings
          </h2>
          <p className="text-sm text-gray-500 mt-1">Configure weatherBOT behavior, IoT connections, and MCP capabilities.</p>
        </div>
        <button id="refresh-status-btn" onClick={fetchStatus} className="p-2 text-gray-400 hover:text-gray-600 rounded-lg hover:bg-gray-100 transition-colors">
          <RefreshCw className="w-4 h-4" />
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* System Mode */}
        <div className="bg-white rounded-xl border shadow-sm p-6 space-y-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Activity className="w-5 h-5 text-indigo-500" />
            System Mode
          </h3>
          <p className="text-sm text-gray-500">Select how the AI should fuse data streams for inference.</p>
          <div className="space-y-3">
            {[
              { id: 'Historical Data Mode', desc: 'Ignore live edge stations. Focus entirely on CSV uploaded datasets.' },
              { id: 'Live Station Mode', desc: 'Ignore historical CSV data. Use GNN to map spatial edge sensor telemetry.' },
              { id: 'Prime', desc: 'Ultimate Hybrid. Fuse historical CSV and live Edge GNN inputs.' },
            ].map(mode => (
              <label
                key={mode.id}
                className={`flex items-start p-4 border rounded-lg cursor-pointer transition-colors ${systemMode === mode.id ? 'bg-blue-50 border-blue-200' : 'hover:bg-gray-50'}`}
              >
                <input
                  type="radio"
                  name="system_mode"
                  value={mode.id}
                  checked={systemMode === mode.id}
                  onChange={e => setSystemMode(e.target.value)}
                  className="mt-1 mr-3 text-blue-600 focus:ring-blue-500"
                />
                <div>
                  <h4 className="font-medium text-gray-900">{mode.id === 'Prime' ? 'Prime Mode (Default)' : mode.id}</h4>
                  <p className="text-sm text-gray-500 mt-1">{mode.desc}</p>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* IoT Status */}
        <div className="bg-white rounded-xl border shadow-sm p-6 space-y-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            {iotStatus?.connected ? <Wifi className="w-5 h-5 text-emerald-500" /> : <WifiOff className="w-5 h-5 text-gray-400" />}
            Weather Station (IoT)
          </h3>

          {/* Status badges */}
          <div className="flex items-center gap-2">
            <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium ${iotStatus?.connected ? 'bg-emerald-100 text-emerald-700' : 'bg-gray-100 text-gray-600'}`}>
              <span className={`w-1.5 h-1.5 rounded-full ${iotStatus?.connected ? 'bg-emerald-500 animate-pulse' : 'bg-gray-400'}`} />
              {iotStatus?.connected ? 'Connected' : 'Disconnected'}
            </span>
            <span className="text-xs text-gray-500 bg-gray-50 px-2 py-1 rounded-full">
              {sourceLabel[iotStatus?.source || 'simulator'] || iotStatus?.source}
            </span>
          </div>

          {/* Live reading */}
          {iotReading && (
            <div className="grid grid-cols-3 gap-2">
              {[
                { label: '🌡️ Temp', value: `${iotReading.temperature}°C` },
                { label: '💧 Humidity', value: `${iotReading.humidity}%` },
                { label: '📊 Pressure', value: `${iotReading.pressure} hPa` },
                { label: '💨 Wind', value: `${iotReading.wind_speed} m/s` },
                { label: '🌧️ Rain', value: `${iotReading.rainfall} mm` },
                { label: '☀️ Light', value: `${iotReading.light_intensity} lux` },
              ].map(item => (
                <div key={item.label} className="bg-gray-50 rounded-lg p-2 text-center">
                  <p className="text-[10px] text-gray-500">{item.label}</p>
                  <p className="text-sm font-semibold text-gray-800">{item.value}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Raspberry Pi Connection */}
        <div className="bg-white rounded-xl border shadow-sm p-6 space-y-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Cpu className="w-5 h-5 text-orange-500" />
            Raspberry Pi Connection
          </h3>

          {/* Serial */}
          <div className="space-y-2">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">USB Serial (UART)</p>
            <div className="flex gap-2">
              <input
                id="serial-port-input"
                value={serialPort}
                onChange={e => setSerialPort(e.target.value)}
                placeholder="COM3 or /dev/ttyUSB0"
                className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
              <input
                id="serial-baud-input"
                type="number"
                value={serialBaud}
                onChange={e => setSerialBaud(Number(e.target.value))}
                placeholder="9600"
                className="w-24 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
              <button
                id="connect-serial-btn"
                onClick={handleConnectSerial}
                disabled={connecting}
                className="px-3 py-2 bg-orange-500 text-white rounded-lg text-sm hover:bg-orange-600 disabled:opacity-50 transition-colors"
              >
                Connect
              </button>
            </div>
          </div>

          {/* MQTT */}
          <div className="space-y-2">
            <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">MQTT (Wireless)</p>
            <div className="flex gap-2">
              <input
                id="mqtt-host-input"
                value={mqttHost}
                onChange={e => setMqttHost(e.target.value)}
                placeholder="192.168.1.100"
                className="flex-1 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
              <input
                id="mqtt-port-input"
                type="number"
                value={mqttPort}
                onChange={e => setMqttPort(Number(e.target.value))}
                placeholder="1883"
                className="w-24 border rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
              />
              <button
                id="connect-mqtt-btn"
                onClick={handleConnectMQTT}
                disabled={connecting}
                className="px-3 py-2 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 disabled:opacity-50 transition-colors"
              >
                Connect
              </button>
            </div>
          </div>

          {connectMsg && (
            <p className="text-sm text-center py-2 px-3 bg-gray-50 rounded-lg border">{connectMsg}</p>
          )}
        </div>

        {/* MCP Tools Viewer */}
        <div className="bg-white rounded-xl border shadow-sm p-6 space-y-4">
          <h3 className="text-lg font-semibold flex items-center gap-2">
            <Zap className="w-5 h-5 text-violet-500" />
            MCP Capabilities
          </h3>
          {mcpTools ? (
            <>
              <div className="flex items-center gap-3 text-sm">
                <span className="bg-violet-100 text-violet-700 px-2 py-0.5 rounded-full text-xs font-medium">
                  v{mcpTools.mcp_version}
                </span>
                <span className="text-gray-500">{mcpTools.total_tools} tools available</span>
              </div>
              <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                {mcpTools.services && Object.entries(mcpTools.services as Record<string, string[]>).map(([svc, actions]) => (
                  <div key={svc} className="flex items-start gap-2">
                    <span className="text-xs font-mono font-bold text-violet-600 w-20 flex-shrink-0 mt-0.5">{svc}</span>
                    <div className="flex flex-wrap gap-1">
                      {actions.map((action: string) => (
                        <span key={action} className="text-[10px] bg-gray-100 text-gray-600 px-1.5 py-0.5 rounded font-mono">
                          {action}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : (
            <p className="text-sm text-gray-400">Loading MCP tools...</p>
          )}
        </div>

        {/* Security Info */}
        <div className="bg-white rounded-xl border shadow-sm p-6 lg:col-span-2">
          <h3 className="text-lg font-semibold flex items-center gap-2 mb-4">
            <Shield className="w-5 h-5 text-emerald-500" />
            Security & Authentication
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-emerald-50 text-emerald-700 p-4 rounded-lg text-sm border border-emerald-100">
              <p className="font-semibold mb-1">Auth Standard</p>
              <p>JWT (JSON Web Token)</p>
            </div>
            <div className="bg-blue-50 text-blue-700 p-4 rounded-lg text-sm border border-blue-100">
              <p className="font-semibold mb-1">Password Hashing</p>
              <p>bcrypt</p>
            </div>
            <div className="bg-violet-50 text-violet-700 p-4 rounded-lg text-sm border border-violet-100">
              <p className="font-semibold mb-1">Edge Isolation</p>
              <p>No internet access · Local only</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Settings;
