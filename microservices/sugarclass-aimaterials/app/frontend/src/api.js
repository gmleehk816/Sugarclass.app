import axios from 'axios';

// Base path for production routing (nginx routes /services/aimaterials/api/* to backend)
const BASE_PATH = '/services/aimaterials';

// Determine if we're in development or production
// Check if we're on localhost or in production domain
const isProduction = !(
  window.location.hostname === 'localhost' ||
  window.location.hostname === '127.0.0.1' ||
  window.location.hostname.startsWith('192.168.') ||
  window.location.port // has a port (common in dev)
);

// Create axios instance
// In production: use BASE_PATH so nginx can route to backend
// In development: no baseURL needed, vite proxy handles routing
const api = axios.create({
  baseURL: isProduction ? BASE_PATH : ''
});

// Request interceptor - only needed in production
api.interceptors.request.use((config) => {
  // In production, prepend BASE_PATH to API requests
  // In development, let requests pass through to vite proxy
  if (isProduction && config.url?.startsWith('/api/')) {
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
console.log('Environment:', isProduction ? 'production' : 'development');
console.log('Hostname:', window.location.hostname);
console.log('Port:', window.location.port || 'none');
console.log('Pathname:', window.location.pathname);
console.log('BASE_PATH:', BASE_PATH);
console.log('baseURL:', isProduction ? BASE_PATH : '(none - using vite proxy)');
console.log('==========================================');

export { api };
