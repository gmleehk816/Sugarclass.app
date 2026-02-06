import axios from 'axios';

// Dynamically determine base URL from environment or current location
// In production: https://sugarclass.app/services/aimaterials -> /services/aimaterials
// In development: http://localhost:3404 -> /services/aimaterials
const getBaseURL = () => {
  // Try environment variable first (set during build)
  if (import.meta.env.VITE_BASE_PATH) {
    return import.meta.env.VITE_BASE_PATH;
  }

  // Fallback: derive from current location
  const pathname = window.location.pathname;

  // Check if we're under /services/aimaterials/
  if (pathname.includes('/services/aimaterials')) {
    return '/services/aimaterials';
  }

  // Default for local development
  return '/services/aimaterials';
};

// Create axios instance with base URL for correct routing
// Base URL should be the app's base path, API calls include /api/ already
export const api = axios.create({
  baseURL: getBaseURL()
});

// Log for debugging
if (import.meta.env.DEV) {
  console.log('API baseURL:', getBaseURL());
}
