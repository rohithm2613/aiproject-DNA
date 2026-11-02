import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Essential for HttpOnly cookie authentication
  timeout: 15000,
});

// Attach bearer token if stored in memory/sessionStorage (dual cookie + bearer support)
api.interceptors.request.use((config) => {
  const token = sessionStorage.getItem('projectdna_token');
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response ? error.response.status : null;
    const message = error.response?.data?.detail || error.message || 'API request failed';

    // Don't warn for expected unauthenticated checks on /auth/me during cold start
    if (status === 401 && error.config?.url?.includes('/auth/me')) {
      return Promise.reject(error);
    }

    console.warn(`[API ${status || 'Network Error'}]`, message);
    return Promise.reject(error);
  }
);

export default api;
