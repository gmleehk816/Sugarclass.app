import axios from 'axios';

// Create axios instance with base URL for correct routing
// Base URL should be the app's base path, API calls include /api/ already
export const api = axios.create({
  baseURL: import.meta.env.VITE_BASE_PATH || '/services/aimaterials'
});
