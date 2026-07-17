import axios from 'axios';

export const api = axios.create({
  baseURL: '/api',
});

export const setAuthToken = (token: string) => {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
};

// ── Datasets ──────────────────────────────────────────────────────────────────
export const uploadDataset = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/datasets/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
};
export const getDatasets = async () => (await api.get('/datasets/')).data;
export const deleteDataset = async (datasetId: number) => (await api.delete(`/datasets/${datasetId}`)).data;

// ── Chat / History ────────────────────────────────────────────────────────────
export const createSession = async (title: string) => (await api.post('/chat/sessions', { title })).data;
export const getSessions = async () => (await api.get('/chat/sessions')).data;
export const deleteSession = async (sessionId: string) => (await api.delete(`/chat/sessions/${sessionId}`)).data;
export const deleteAllSessions = async () => (await api.delete(`/chat/sessions`)).data;
export const sendMessage = async (sessionId: string, content: string, isOnline: boolean, systemMode: string = 'Prime') =>
  (await api.post(`/chat/sessions/${sessionId}/message`, { role: 'user', content, is_online: isOnline, system_mode: systemMode })).data;
export const getMessages = async (sessionId: string) => (await api.get(`/chat/sessions/${sessionId}/messages`)).data;
export const getSessionXAI = async (sessionId: string) => (await api.get(`/chat/sessions/${sessionId}/xai`)).data;
export const getHistoryStats = async () => (await api.get('/chat/stats')).data;
export const searchHistory = async (query: string) => (await api.get(`/chat/search?q=${encodeURIComponent(query)}`)).data;

// ── Predictions ───────────────────────────────────────────────────────────────
export const getLivePrediction = async (nNodes: number = 3) =>
  (await api.get(`/predictions/live?n_nodes=${nNodes}`)).data;
export const getHistoricalPrediction = async () => (await api.get('/predictions/historical')).data;
export const getRecommendations = async (intent: string = 'GENERAL_CHAT', systemMode: string = 'prime') =>
  (await api.get(`/predictions/recommendations?intent=${intent}&system_mode=${systemMode}`)).data;
export const getXAI = async () => (await api.get('/predictions/xai')).data;

// ── MCP ───────────────────────────────────────────────────────────────────────
export const getMCPTools = async () => (await api.get('/mcp/tools')).data;
export const routeMCP = async (service: string, action: string, params: Record<string, unknown> = {}) =>
  (await api.post('/mcp/route', { service, action, params })).data;
export const getIoTStatus = async () => (await api.get('/mcp/iot/status')).data;
export const getIoTReading = async () => (await api.get('/mcp/iot/reading')).data;
export const connectSerial = async (port: string, baud: number) =>
  (await api.post(`/mcp/iot/connect/serial?port=${port}&baud=${baud}`)).data;
export const connectMQTT = async (host: string, port: number) =>
  (await api.post(`/mcp/iot/connect/mqtt?host=${host}&port=${port}`)).data;

export default api;
