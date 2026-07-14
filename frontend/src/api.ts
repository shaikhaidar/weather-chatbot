import axios from 'axios';

export const api = axios.create({
  baseURL: 'http://localhost:8000/api',
});

export const setAuthToken = (token: string) => {
  api.defaults.headers.common['Authorization'] = `Bearer ${token}`;
};

export const uploadDataset = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/datasets/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getDatasets = async () => {
  const response = await api.get('/datasets/');
  return response.data;
};

export const createSession = async (title: string) => {
  const response = await api.post('/chat/sessions', { title });
  return response.data;
};

export const getSessions = async () => {
  const response = await api.get('/chat/sessions');
  return response.data;
};

export const sendMessage = async (sessionId: string, content: string, isOnline: boolean, systemMode: string = "Prime") => {
  const response = await api.post(`/chat/sessions/${sessionId}/message`, { role: 'user', content, is_online: isOnline, system_mode: systemMode });
  return response.data;
};

export const getMessages = async (sessionId: string) => {
  const response = await api.get(`/chat/sessions/${sessionId}/messages`);
  return response.data;
};

export default api;
