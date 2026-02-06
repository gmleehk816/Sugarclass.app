import axios from 'axios';

// Always use /services/aimaterials as base URL
// This works in both development and production
const BASE_PATH = '/services/aimaterials';

// Create axios instance
const api = axios.create({
  baseURL: BASE_PATH
});

// Request interceptor to prepend base path to all API requests
api.interceptors.request.use((config) => {
  // If URL starts with /api/, prepend the base path
  if (config.url?.startsWith('/api/')) {
    config.url = `${BASE_PATH}${config.url}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Log base URL for debugging (always log to help debug production)
console.log('API BASE_PATH:', BASE_PATH);
console.log('Window location:', window.location.href);
console.log('Import meta env.VITE_BASE_PATH:', import.meta.env.VITE_BASE_PATH);

export { api };
