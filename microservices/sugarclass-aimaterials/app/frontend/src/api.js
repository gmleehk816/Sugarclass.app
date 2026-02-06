import axios from 'axios';

// Base path for production routing (nginx routes /services/aimaterials/api/* to backend)
const BASE_PATH = '/services/aimaterials';

// Determine if we're in development or production
// We're in production if accessing via domain (not localhost/local IP)
const hostname = window.location.hostname;
const isProduction = !(
  hostname === 'localhost' ||
  hostname === '127.0.0.1' ||
  hostname.startsWith('192.168.') ||
  hostname.startsWith('10.') ||
  hostname.startsWith('172.16.') ||
  hostname.endsWith('.local') ||
  hostname.endsWith('.localhost')
);

// DEBUG: Log environment detection immediately
console.log('=== API CLIENT INITIALIZATION ===');
console.log('hostname:', hostname);
console.log('isProduction:', isProduction);
console.log('willPrependBasePath:', isProduction);
console.log('==================================');

// Create axios instance
const api = axios.create({
  baseURL: isProduction ? BASE_PATH : ''
});

// Request interceptor - CRITICAL for production
api.interceptors.request.use((config) => {
  const originalUrl = config.url;

  // In production, ALWAYS prepend BASE_PATH to /api/ requests
  // This is required because nginx expects /services/aimaterials/api/*
  if (isProduction && config.url?.startsWith('/api/')) {
    config.url = `${BASE_PATH}${config.url}`;
  }

  // Log for debugging
  console.log(`[API Request] ${originalUrl} → ${config.url}`);

  return config;
}, (error) => {
  console.error('[API Request Error]', error);
  return Promise.reject(error);
});

// Response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log(`[API Response] ${response.config.url} - ${response.status}`);
    return response;
  },
  (error) => {
    const url = error.config?.url || 'unknown';
    const status = error.response?.status || 'network error';
    console.error(`[API Error] ${url} - ${status}`, error.message);
    return Promise.reject(error);
  }
);

export { api, isProduction, BASE_PATH };
