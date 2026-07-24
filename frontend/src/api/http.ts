import axios from 'axios';

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? '/api/v1';

export const http = axios.create({
  baseURL: apiBaseUrl,
  timeout: 10000,
});

http.interceptors.request.use((config) => {
  const token = localStorage.getItem('reportflow_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 403) {
      localStorage.removeItem('reportflow_token');
      localStorage.removeItem('reportflow_user');
    }
    const message = error?.response?.data?.message;
    if (typeof message === 'string' && message) {
      return Promise.reject(new Error(message));
    }
    return Promise.reject(error);
  },
);
