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
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Log configuration for debugging
console.log('API Configuration:');
console.log('  Environment:', isDev ? 'development' : 'production');
console.log('  BASE_PATH:', BASE_PATH);
console.log('  baseURL:', isDev ? '(none - using vite proxy)' : BASE_PATH);
console.log('  Window location:', window.location.href);

export { api };
