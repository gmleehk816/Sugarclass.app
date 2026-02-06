import axios from 'axios';

// Base path for production routing (nginx routes /services/aimaterials/api/* to backend)
const BASE_PATH = '/services/aimaterials';

// Determine if we're in development or production
// Check if accessing via localhost/local IP vs production domain
const hostname = window.location.hostname;
const isLocalhost =
  hostname === 'localhost' ||
  hostname === '127.0.0.1' ||
  hostname.startsWith('192.168.') ||
  hostname.startsWith('10.') ||
  hostname.startsWith('172.16.') ||
  hostname.endsWith('.local') ||
  hostname.endsWith('.localhost');

const isProduction = !isLocalhost;

// CRITICAL: Log immediately for debugging
console.log('%c=== AI MATERIALS API CLIENT ===', 'background: #0ea5e9; color: white; padding: 4px 8px; border-radius: 4px;');
console.log('Hostname:', hostname);
console.log('Is Localhost:', isLocalhost);
console.log('Is Production:', isProduction);
console.log('Base Path:', BASE_PATH);
console.log('%c================================', 'background: #0ea5e9; color: white; padding: 4px 8px; border-radius: 4px;');

// Create axios instance
const api = axios.create({
  baseURL: isProduction ? BASE_PATH : ''
});

// Request interceptor - ALWAYS prepend BASE_PATH for /api/ calls in production
api.interceptors.request.use((config) => {
  const originalUrl = config.url;

  // CRITICAL: In production (including iframe), prepend BASE_PATH to /api/ requests
  if (isProduction && config.url?.startsWith('/api/')) {
    config.url = `${BASE_PATH}${config.url}`;
    console.log(`%c[API] ${originalUrl} → ${config.url}`, 'color: #22c55e;');
  } else {
    console.log(`[API] ${config.url}`);
  }

  return config;
}, (error) => {
  console.error('%c[API Request Error]', 'color: #ef4444;', error);
  return Promise.reject(error);
});

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`%c[API Response] ${response.config.url} - ${response.status}`, 'color: #3b82f6;');
    // Log response data for debugging
    if (response.config.url?.includes('/subjects')) {
      console.log('[Response Data]', response.data);
      console.log('[Response Data Type]', typeof response.data);
      console.log('[Is Array]', Array.isArray(response.data));
    }
    return response;
  },
  (error) => {
    const url = error.config?.url || 'unknown';
    const status = error.response?.status || 'network error';
    console.error(`%c[API Error] ${url} - ${status}`, 'color: #ef4444;', error.message);
    if (error.response?.data) {
      console.log('[Error Response Data]', error.response.data);
    }
    return Promise.reject(error);
  }
);

export { api, isProduction, BASE_PATH };
