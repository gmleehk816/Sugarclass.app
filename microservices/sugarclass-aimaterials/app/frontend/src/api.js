import axios from 'axios';

// Base path for production routing (nginx routes /services/aimaterials/api/* to backend)
const BASE_PATH = '/services/aimaterials';

// Determine if we're in development or production
const isDev = import.meta.env.DEV;

// Create axios instance
// In production: use BASE_PATH so nginx can route to backend
// In development: no baseURL needed, vite proxy handles routing
const api = axios.create({
  baseURL: isDev ? '' : BASE_PATH
});

// Request interceptor - only needed in production
api.interceptors.request.use((config) => {
  // In production, prepend BASE_PATH to API requests
  // In development, let requests pass through to vite proxy
  if (!isDev && config.url?.startsWith('/api/')) {
    config.url = `${BASE_PATH}${config.url}`;
  }
  // Log API calls for debugging
  console.log(`[API Call] ${config.method?.toUpperCase()} ${config.url}`);
  return config;
}, (error) => {
  console.error('[API Error]', error);
  return Promise.reject(error);
});

// Response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log(`[API Response] ${response.config.url} - Status: ${response.status}`);
    return response;
  },
  (error) => {
    console.error(`[API Error] ${error.config?.url} - Status: ${error.response?.status}`, error.message);
    return Promise.reject(error);
  }
);

// Log configuration for debugging
console.log('=== AI Materials API Configuration ===');
console.log('Environment:', isDev ? 'development' : 'production');
console.log('BASE_PATH:', BASE_PATH);
console.log('VITE_BASE_PATH from env:', import.meta.env.VITE_BASE_PATH);
console.log('VITE_API_URL from env:', import.meta.env.VITE_API_URL);
console.log('baseURL:', isDev ? '(none - using vite proxy)' : BASE_PATH);
console.log('Window location:', window.location.href);
console.log('==========================================');

export { api };
