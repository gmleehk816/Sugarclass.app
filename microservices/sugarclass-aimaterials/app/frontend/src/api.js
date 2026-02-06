import axios from 'axios';

// Always use /services/aimaterials as base URL
// This works in both development and production
const BASE_URL = '/services/aimaterials';

// Create axios instance with base URL for correct routing
export const api = axios.create({
  baseURL: BASE_URL
});

// Log base URL for debugging (always log to help debug production)
console.log('API baseURL:', BASE_URL);
console.log('Window location:', window.location.href);
console.log('Import meta env.VITE_BASE_PATH:', import.meta.env.VITE_BASE_PATH);
